import re,os,time,md5
from django.db import models
from noc.setup.models import Settings
from noc.ip.models import IPv4Address
from noc.lib.validators import is_ipv4

class DNSZoneProfile(models.Model):
    class Admin:
        pass
    class Meta:
        pass
    name=models.CharField("Name",maxlength=32,unique=True)
    zone_transfer_acl=models.CharField("named zone transfer ACL",maxlength=64)
    zone_ns_list=models.CharField("NS list",maxlength=64)
    zone_soa=models.CharField("SOA",maxlength=64)
    zone_contact=models.CharField("Contact",maxlength=64)
    zone_refresh=models.IntegerField("Refresh",default=3600)
    zone_retry=models.IntegerField("Retry",default=900)
    zone_expire=models.IntegerField("Expire",default=86400)
    zone_ttl=models.IntegerField("TTL",default=3600)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @classmethod
    def pretty_time(cls,t):
        if t==0:
            return "zero"
        T=["week","day","hour","min","sec"]
        W=[345600,86400,3600,60,1]
        r=[]
        for w in W:
            rr=int(t/w)
            t-=rr*w
            r.append(rr)
        z=[]
        for rr,t in zip(r,T):
            if rr>1:
                z.append("%d %ss"%(rr,t))
            elif rr>0:
                z.append("%d %s"%(rr,t))
        return " ".join(z)

    def _ztacl(self):
        return "allow-transfer { %s; };"%self.zone_transfer_acl.replace("}","")
    ztacl=property(_ztacl)

rx_rzone=re.compile(r"^(\d+)\.(\d+)\.(\d+)\.in-addr.arpa$")
class DNSZone(models.Model):
    class Admin:
        list_display=["name","description","is_auto_generated"]
        list_filter=["is_auto_generated"]
        search_fields=["name","description"]
    class Meta:
        verbose_name="DNS Zone"
        verbose_name_plural="DNS Zones"
    name=models.CharField("Domain",maxlength=64,unique=True)
    description=models.CharField("Description",null=True,blank=True,maxlength=64)
    is_auto_generated=models.BooleanField("Auto generated?")
    serial=models.CharField("Serial",maxlength=10,default="0000000000")
    profile=models.ForeignKey(DNSZoneProfile,verbose_name="Profile")
    def __str__(self):
        return self.name
    def __unicode__(self):
        return self.name
    def _type(self):
        if self.name.endswith(".in-addr.arpa"):
            return "R"
        else:
            return "F"
    type=property(_type)
    def _reverse_prefix(self):
        match=rx_rzone.match(self.name)
        if match:
            return "%s.%s.%s.0/24"%(match.group(3),match.group(2),match.group(1))
    reverse_prefix=property(_reverse_prefix)
    def _file_name(self):
        return self.name
    file_name=property(_file_name)
    def _path(self):
        return os.path.join(Settings.get("dns.zone_cache"),self.file_name)
    path=property(_path)
    def _next_serial(self):
        T=time.gmtime()
        p="%04d%02d%02d"%(T[0],T[1],T[2])
        sn=int(self.serial[-2:])
        if self.serial.startswith(p):
            return p+"%02d"%(sn+1)
        return p+"00"
    next_serial=property(_next_serial)
    def _zonedata(self):
        from django.db import connection
        c=connection.cursor()
        if self.type=="F":
            c.execute("SELECT hostname(fqdn),ip FROM %s WHERE domainname(fqdn)=%%s ORDER BY ip"%IPv4Address._meta.db_table, [self.name])
            records=[[r[0],"IN  A",r[1]] for r in c.fetchall()]
        elif self.type=="R":
            c.execute("SELECT ip,fqdn FROM %s WHERE ip::cidr << %%s ORDER BY ip"%IPv4Address._meta.db_table,[self.reverse_prefix])
            records=[[r[0].split(".")[3],"PTR",r[1]+"."] for r in c.fetchall()]
        else:
            raise Exception,"Invalid zone type"
        # Add records from DNSZoneRecord
        zonerecords=self.dnszonerecord_set.all()
        if self.type=="R":
            # Subnet delegation macro
            delegations={}
            for d in [r for r in zonerecords if "NS" in r.type.type and "/" in r.left]:
                r=d.right
                l=d.left
                if l in delegations:
                    delegations[l].append(r)
                else:
                    delegations[l]=[r]
            for d,nses in delegations.items():
                try:
                    net,mask=[int(x) for x in l.split("/")]
                    if net<0 or net>255 or mask<=24 or mask>32:
                        raise Exception,"Invalid record"
                except:
                    records+=[[";; Invalid record: %s"%d,"IN NS","error"]]
                    continue
                for ns in nses:
                    records+=[[d,"IN NS",ns]]
                m=mask-24
                bitmask=((1<<m)-1)<<(8-m)
                if net&bitmask != net:
                    records+=[[";; Invalid network: %s"%d,"CNAME",d]]
                    continue
                for i in range(net,net+(1<<(8-m))):
                    records+=[["%d"%i,"CNAME","%d.%s"%(i,d)]]
            # Other records
            records+=[[x.left,x.type.type,x.right] for x in zonerecords\
                if ("NS" in x.type.type and "/" not in x.left) or "NS" not in x.type.type]
        else:
            records+=[[x.left,x.type.type,x.right] for x in zonerecords]
        # Add NS records if nesessary
        l=len(self.name)
        for z in self.children:
            for ns in z.ns_list:
                records+=[[z.name[:-l-1],"IN NS",ns]]
        records.sort(lambda x,y:cmp(x[0],y[0]))
        nses=["\tNS\t%s\n"%n for n in self.ns_list]
        nses="".join(nses)
        contact=self.profile.zone_contact.replace("@",".")
        if not contact.endswith("."):
            contact+="."
        s=""";;
;; WARNING: Auto-generated zone file
;; Do not edit manually
;;
$ORIGIN .
$TTL %(ttl)d
%(domain)s IN SOA %(soa)s %(contact)s (
            %(serial)s ; serial
            %(refresh)d       ; refresh (%(pretty_refresh)s)
            %(retry)d        ; retry (%(pretty_retry)s)
            %(expire)d    ; expire (%(pretty_expire)s)
            %(ttl)d       ; minimum (%(pretty_ttl)s)
            )
%(nses)s
$ORIGIN %(domain)s.
"""%{"domain":self.name,
        "soa":self.profile.zone_soa,
        "contact":contact,
        "serial":self.serial,
        "ttl":self.profile.zone_ttl,"pretty_ttl":DNSZoneProfile.pretty_time(self.profile.zone_ttl),
        "refresh":self.profile.zone_refresh,"pretty_refresh":DNSZoneProfile.pretty_time(self.profile.zone_refresh),
        "retry":self.profile.zone_retry,"pretty_retry":DNSZoneProfile.pretty_time(self.profile.zone_retry),
        "expire":self.profile.zone_expire,"pretty_expire":DNSZoneProfile.pretty_time(self.profile.zone_expire),
        "nses":nses
        }
        maxlen=10
        records=[r for r in records if len(r)==3]
        for a,b,c in records:
            l=len(a)
            if l>maxlen:
                maxlen=l
        mask="%%-%ds %%-6s %%s"%maxlen
        s+="\n".join([mask%tuple(r) for r in records if len(r)==3])
        s+="""
;;
;; End of auto-generated zone
;;
"""
        return s
    zonedata=property(_zonedata)
    def rewrite_zone(self):
        path=self.path
        zd=self.zonedata
        if DNSZone.is_differ(path,zd):
            self.serial=self.next_serial
            self.save()
            f=open(path,"w")
            f.write(self.zonedata)
            f.close()
    @classmethod
    def rewrite_zones(cls):
        s="""#
# WARNING: This is auto-generated file
# Do not edit manually
#
"""
        for z in DNSZone.objects.filter(is_auto_generated=True):
            z.rewrite_zone()
            s+="""zone "%(zone)s" {
    type master;
    file "autozones/%(filename)s";
    allow-transfer { acl-backup-ns; };
};

"""%{"zone":z.name,"filename":z.file_name}
        s+="""#
# End of auto-generated file
#
"""
        path=os.path.join(Settings.get("dns.zone_cache"),"autozones.conf")
        if DNSZone.is_differ(path,s):
            f=open(path,"w")
            f.write(s)
            f.close()
            
    @classmethod
    def sync_zones(cls):
        cls.rewrite_zones()
        os.environ["RSYNC_RSH"]=Settings.get("shell.ssh")
        os.chdir(Settings.get("dns.zone_cache"))
        os.system("%s -av --delete * %s"%(Settings.get("shell.rsync"),Settings.get("dns.rsync_target")))

    @classmethod
    def is_differ(cls,path,s):
        if os.path.isfile(path):
            f=open(path)
            cs1=md5.md5(f.read()).hexdigest()
            f.close()
            cs2=md5.md5(s).hexdigest()
            return cs2!=cs1
        else:
            return True
            
    def _children(self):
        l=len(self.name)
        return [z for z in DNSZone.objects.filter(name__iendswith="."+self.name) if "." not in z.name[:-l-1]]
    children=property(_children)
    
    def _ns_list(self):
        nses=[]
        for ns in self.profile.zone_ns_list.split(","):
            ns=ns.strip()
            if not is_ipv4(ns) and not ns.endswith("."):
                ns+="."
            nses.append(ns)
        return nses
    ns_list=property(_ns_list)
            
class DNSZoneRecordType(models.Model):
    class Admin:
        list_display=["type"]
        search_fields=["type"]
    class Meta:
        verbose_name="DNS Zone Record Type"
        verbose_name_plural="DNS Zone Record Types"
    type=models.CharField("Type",maxlength=16,unique=True)
    def __str__(self):
        return self.type
    def __unicode__(self):
        return unicode(self.type)
        
class DNSZoneRecord(models.Model):
    class Admin: pass
    class Meta: pass
    zone=models.ForeignKey(DNSZone,verbose_name="Zone",edit_inline=models.TABULAR,num_extra_on_change=5)
    left=models.CharField("Left",maxlength=32,blank=True,null=True)
    type=models.ForeignKey(DNSZoneRecordType,verbose_name="Type")
    right=models.CharField("Right",maxlength=64,core=True)
    def __str__(self):
        return "%s %s"%(self.zone.name," ".join([x for x in [self.left,self.type.type,self.right] if x is not None]))
    def __unicode__(self):
        return unicode(str(self))