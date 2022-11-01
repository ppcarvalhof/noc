# ----------------------------------------------------------------------
# SegmentTopology class
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import operator
import logging
import itertools
from collections import defaultdict
from typing import Dict, List, Set, Optional, Iterable

# Third-party modules
import cachetools
from bson import ObjectId

# NOC modules
from noc.core.stencil import stencil_registry, Stencil
from noc.core.log import PrefixLoggerAdapter
from noc.core.ip import IP
from noc.core.graph.nexthop import iter_next_hops
from noc.sa.models.managedobject import ManagedObject
from noc.inv.models.networksegment import NetworkSegment
from noc.inv.models.interface import Interface
from noc.inv.models.link import Link
from ..types import ShapeOverlay, ShapeOverlayPosition, ShapeOverlayForm
from ..base import TopologyBase, MapItem

logger = logging.getLogger(__name__)


class SegmentTopology(TopologyBase):
    name = "segment"
    header = "Network Segment Schemas"
    CAPS: Set[str] = {"Network | STP"}

    def __init__(self, gen_id, node_hints=None, link_hints=None, force_spring=False):
        self.segment = NetworkSegment.get_by_id(gen_id)
        self.logger = PrefixLoggerAdapter(logger, self.segment.name)
        self.segment_siblings = self.segment.get_siblings()
        self._uplinks_cache = {}
        self.segment_objects = set()
        if self.segment.parent:
            self.parent_segment = self.segment.parent
            self.ancestor_segments = set(self.segment.get_path()[:-1])
        else:
            self.parent_segment = None
            self.ancestor_segments = set()
        super().__init__(
            gen_id, node_hints=node_hints, link_hints=link_hints, force_spring=force_spring
        )

    @property
    def title(self):
        return self.segment.name

    def get_role(self, mo: ManagedObject) -> str:
        if mo.segment in self.segment_siblings:
            return "segment"
        elif self.parent_segment and mo.segment.id in self.ancestor_segments:
            return "uplink"
        else:
            return "downlink"

    @cachetools.cachedmethod(operator.attrgetter("_uplinks_cache"))
    def get_uplinks(self) -> List[str]:
        self.logger.info("Searching for uplinks")
        if not self.G:
            return []
        for policy in self.segment.profile.iter_uplink_policy():
            uplinks = getattr(self, f"get_uplinks_{policy}")()
            if uplinks:
                self.logger.info(
                    "[%s] %d uplinks found: %s",
                    policy,
                    len(uplinks),
                    ", ".join(str(x) for x in uplinks),
                )
                return uplinks
            self.logger.info("[%s] No uplinks found. Skipping", policy)
        self.logger.info("Failed to find uplinks")
        return []

    def get_uplinks_seghier(self) -> List[str]:
        """
        Find uplinks basing on segment hierarchy. Any object with parent segment
        is uplink
        :return:
        """
        return [i for i in self.G.nodes if self.G.nodes[i].get("role") == "uplink"]

    def get_uplinks_molevel(self) -> List[str]:
        """
        Find uplinks basing on Managed Object's level. Top-leveled objects are returned.
        :return:
        """
        max_level = max(
            self.G.nodes[i].get("level")
            for i in self.G.nodes
            if self.G.nodes[i].get("type") == "managedobject"
        )
        return [
            i
            for i in self.G.nodes
            if self.G.nodes[i].get("type") == "managedobject"
            and self.G.nodes[i].get("level") == max_level
        ]

    def get_uplinks_seg(self) -> List[str]:
        """
        All segment objects are uplinks
        :return:
        """
        return [i for i in self.G.nodes if self.G.nodes[i].get("role") == "segment"]

    def get_uplinks_minaddr(self) -> List[str]:
        """
        Segment's Object with lesser address is uplink
        :return:
        """
        s = next(
            iter(
                sorted(
                    (IP.prefix(self.G.nodes[i].get("address")), i)
                    for i in self.G.nodes
                    if self.G.nodes[i].get("role") == "segment"
                )
            )
        )
        return [s[1]]

    def get_uplinks_maxaddr(self) -> List[str]:
        """
        Segment's Object with greater address is uplink
        :return:
        """
        s = next(
            reversed(
                sorted(
                    (IP.prefix(self.G.nodes[i].get("address")), i)
                    for i in self.G.nodes
                    if self.G.nodes[i].get("role") == "segment"
                )
            )
        )
        return [s[1]]

    def get_node_stencil(
        self, o: ManagedObject, node_type: Optional[str] = None
    ) -> Optional[Stencil]:
        """
        Get ManagedObejct Stencil

        :param o: ManagedObject
        :param node_type:
        :return:
        """
        if node_type == "cloud":
            return stencil_registry.get(o.shape or stencil_registry.DEFAULT_CLOUD_STENCIL)
        if o.shape:
            # Use mo's shape, if set
            return stencil_registry.get(o.shape)
        elif o.object_profile.shape:
            # Use profile's shape
            return stencil_registry.get(o.object_profile.shape)
        return stencil_registry.get(stencil_registry.DEFAULT_STENCIL)

    def get_node_stencil_overlays(
        self, mo: ManagedObject, node_type: Optional[str] = None
    ) -> List[ShapeOverlay]:
        """

        :param mo:
        :param node_type:
        :return:
        """
        if node_type == "cloud":
            return []
        seen: Set[ShapeOverlayPosition] = set()
        r: List[ShapeOverlay] = []
        # ManagedObject
        if mo.shape_overlay_glyph:
            pos = mo.shape_overlay_position or ShapeOverlayPosition.NW
            r += [
                ShapeOverlay(
                    code=mo.shape_overlay_glyph.code,
                    position=pos,
                    form=mo.shape_overlay_form or ShapeOverlayForm.Circle,
                )
            ]
            seen.add(pos)
        # Project
        if mo.project and mo.project.shape_overlay_glyph:
            pos = mo.project.shape_overlay_position or ShapeOverlayPosition.NW
            if pos not in seen:
                r += [
                    ShapeOverlay(
                        code=mo.project.shape_overlay_glyph.code,
                        position=pos,
                        form=mo.project.shape_overlay_form or ShapeOverlayForm.Circle,
                    )
                ]
                seen.add(pos)
        # ManagedObjectProfile
        if mo.object_profile.shape_overlay_glyph:
            pos = mo.object_profile.shape_overlay_position or ShapeOverlayPosition.NW
            if pos not in seen:
                r += [
                    ShapeOverlay(
                        code=mo.object_profile.shape_overlay_glyph.code,
                        position=pos,
                        form=mo.object_profile.shape_overlay_form or ShapeOverlayForm.Circle,
                    )
                ]
                seen.add(pos)
        return r

    def load(self):
        """
        Load all managed objects from segment
        """

        def get_bandwidth(if_list):
            """
            Calculate bandwidth for list of interfaces
            :param if_list:
            :return: total in bandwidth, total out bandwidth
            """
            in_bw = 0
            out_bw = 0
            for iface in if_list:
                bw = iface.get("bandwidth") or 0
                in_speed = iface.get("in_speed") or 0
                out_speed = iface.get("out_speed") or 0
                in_bw += bandwidth(in_speed, bw)
                out_bw += bandwidth(out_speed, bw)
            return in_bw, out_bw

        def bandwidth(speed, if_bw):
            if speed and if_bw:
                return min(speed, if_bw)
            elif speed and not if_bw:
                return speed
            elif if_bw:
                return if_bw
            else:
                return 0

        # Get all links, belonging to segment
        links: List[Link] = list(
            Link.objects.filter(linked_segments__in=[s.id for s in self.segment_siblings])
        )
        # All linked interfaces from map
        all_ifaces: List["ObjectId"] = list(
            itertools.chain.from_iterable(link.interface_ids for link in links)
        )
        # Bulk fetch all interfaces data
        ifs: Dict["ObjectId", "Interface"] = {
            i["_id"]: i
            for i in Interface._get_collection().find(
                {"_id": {"$in": all_ifaces}},
                {
                    "_id": 1,
                    "managed_object": 1,
                    "name": 1,
                    "bandwidth": 1,
                    "in_speed": 1,
                    "out_speed": 1,
                },
            )
        }
        # Bulk fetch all managed objects
        segment_mos: Set[int] = set(self.segment.managed_objects.values_list("id", flat=True))
        all_mos: List[int] = list(
            set(i["managed_object"] for i in ifs.values() if "managed_object" in i) | segment_mos
        )
        mos: Dict[int, "ManagedObject"] = {
            mo.id: mo for mo in ManagedObject.objects.filter(id__in=all_mos)
        }
        self.segment_objects: Set[int] = set(
            mo_id for mo_id in all_mos if mos[mo_id].segment.id == self.segment.id
        )
        for mo in mos.values():
            attrs = {
                "role": self.get_role(mo),
                "address": mo.address,
                "level": mo.object_profile.level,
            }
            if attrs["role"] == "uplink":
                attrs["portal"] = {"generator": "segment", "id": self.parent_segment}
            elif attrs["role"] == "downlink":
                attrs["portal"] = {"generator": "segment", "id": str(mo.segment.id)}
            self.add_node(
                mo,
                "managedobject",
                attrs,
            )
            # self.add_object(mo)
        # Process all segment's links
        pn = 0
        for link in links:
            if link.is_loop:
                continue  # Loops are not shown on map
            # Group interfaces by objects
            # avoiding non-bulk dereferencing
            mo_ifaces = defaultdict(list)
            for if_id in link.interface_ids:
                iface = ifs[if_id]
                mo_ifaces[mos[iface["managed_object"]]] += [iface]
            # Pairs of managed objects are pseudo-links
            if len(mo_ifaces) == 2:
                # ptp link
                pseudo_links = [list(mo_ifaces)]
                is_pmp = False
            else:
                # pmp
                # Create virtual cloud
                self.add_node(link, "cloud")
                # Create virtual links to cloud
                pseudo_links = [(link, mo) for mo in mo_ifaces]
                # Create virtual cloud interface
                mo_ifaces[link] = [{"name": "cloud"}]
                is_pmp = True
            # Link all pairs
            for mo0, mo1 in pseudo_links:
                mo0_id = str(mo0.id)
                mo1_id = str(mo1.id)
                # Create virtual ports for mo0
                self.G.nodes[mo0_id]["ports"] += [
                    {"id": pn, "ports": [i["name"] for i in mo_ifaces[mo0]]}
                ]
                # Create virtual ports for mo1
                self.G.nodes[mo1_id]["ports"] += [
                    {"id": pn + 1, "ports": [i["name"] for i in mo_ifaces[mo1]]}
                ]
                # Calculate bandwidth
                t_in_bw, t_out_bw = get_bandwidth(mo_ifaces[mo0])
                d_in_bw, d_out_bw = get_bandwidth(mo_ifaces[mo1])
                in_bw = bandwidth(t_in_bw, d_out_bw) * 1000
                out_bw = bandwidth(t_out_bw, d_in_bw) * 1000
                # Add link
                if is_pmp:
                    link_id = "%s-%s-%s" % (link.id, pn, pn + 1)
                else:
                    link_id = str(link.id)
                self.add_link(
                    mo0_id,
                    mo1_id,
                    {
                        "id": link_id,
                        "type": "link",
                        "method": link.discovery_method,
                        "ports": [pn, pn + 1],
                        # Target to source
                        "in_bw": in_bw,
                        # Source to target
                        "out_bw": out_bw,
                        # Max bandwidth
                        "bw": max(in_bw, out_bw),
                    },
                )
                pn += 2

    @staticmethod
    def q_mo(d):
        x = d.copy()
        if x["type"] == "managedobject":
            del x["mo"]
            # x["external"] = x["id"] not in mos if is_view else x.get("role") != "segment"
            x["external"] = x.get("role") != "segment"
        elif d["type"] == "cloud":
            del x["link"]
            x["external"] = False
        return x

    def iter_uplinks(self):
        """
        Yields ObjectUplinks items for segment

        :returns: ObjectUplinks items
        """

        def get_node_uplinks(node: str) -> List[str]:
            role = self.G.nodes[node].get("role", "cloud")
            if role == "uplink":
                # Only downlinks matter
                return []
            elif role == "downlink":
                # All segment neighbors are uplinks.
                # As no inter-downlink segment's links are loaded
                # so all neigbors are from current segment
                return list(self.G.neighbors(node))
            # Segment role and clouds
            ups = {}
            for u in uplinks:
                if u == node:
                    # skip self
                    continue
                for next_hop, path_len in iter_next_hops(self.G, node, u):
                    ups[next_hop] = min(path_len, ups.get(next_hop, path_len))
            # Shortest path first
            return sorted(ups, key=lambda x: ups[x])

        from noc.sa.models.managedobject import ObjectUplinks

        uplinks = self.get_uplinks()
        # @todo: Workaround for empty uplinks
        # Get uplinks for cloud nodes
        cloud_uplinks: Dict[str, List[int]] = {
            o: [int(u) for u in get_node_uplinks(o)]
            for o in self.G.nodes
            if self.G.nodes[o]["type"] == "cloud"
        }
        # All objects including neighbors
        all_objects: Set[str] = set(
            o for o in self.G.nodes if self.G.nodes[o]["type"] == "managedobject"
        )
        # Get objects uplinks
        obj_uplinks: Dict[int, List[int]] = {}
        obj_downlinks: Dict[int, Set[int]] = defaultdict(set)
        for o in all_objects:
            mo = int(o)
            ups: List[int] = []
            for u in get_node_uplinks(o):
                cu = cloud_uplinks.get(u)
                if cu is not None:
                    # Uplink is a cloud. Use cloud's uplinks instead
                    ups += cu
                else:
                    ups += [int(u)]
            obj_uplinks[mo] = ups
            for u in ups:
                obj_downlinks[u].add(mo)
        # Check uplinks with DownlinkMerge settings
        dlm_settings: Set[int] = set(
            ManagedObject.objects.filter(
                id__in=obj_uplinks, object_profile__enable_rca_downlink_merge=True
            ).values_list("id", flat=True)
        )
        # Calculate RCA neighbors and yield result
        for mo in obj_uplinks:
            # Filter out only current segment. Neighbors will be updated by their
            # segment's tasks
            if mo not in self.segment_objects:
                continue
            # All uplinks
            neighbors = set(obj_uplinks[mo])
            # All downlinks
            for dmo in obj_downlinks[mo]:
                neighbors.add(dmo)
                # And uplinks of downlinks
                neighbors |= set(obj_uplinks[dmo])
            # Downlinks of uplink if MergeDownlinks setting is set
            if dlm_settings and dlm_settings.intersection(set(obj_uplinks[mo])):
                for dumo in obj_uplinks[mo]:
                    neighbors |= obj_downlinks[dumo]
            # Not including object itself
            if mo in neighbors:
                neighbors.remove(mo)
            #
            rca_neighbors = list(sorted(neighbors))
            # Recalculated result
            yield ObjectUplinks(
                object_id=mo,
                uplinks=obj_uplinks[mo],
                rca_neighbors=rca_neighbors,
            )

    def iter_nodes(self):
        for n in self.G.nodes.values():
            yield self.q_mo(n)

    @classmethod
    def iter_maps(
        cls,
        parent: str = None,
        query: Optional[str] = None,
        limit: Optional[int] = None,
        start: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Iterable[MapItem]:
        data = NetworkSegment.objects.filter(parent=parent).order_by("name")
        if query:
            data = data.filter(name__icontains=query)
        # Apply paging
        if limit:
            data = data[start: start + limit]
        for ns in data:
            yield MapItem(
                title=str(ns.name),
                generator=cls.name,
                id=str(ns.id),
                has_children=ns.has_children,
            )
