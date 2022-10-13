# ---------------------------------------------------------------------
# Set ThresholdProfiles uuid
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

import copy

# NOC modules
from noc.core.migration.base import BaseMigration


class Migration(BaseMigration):
    def migrate(self):
        db = self.mongo_db
        old_linux_profile_id = db.noc.profiles.find(
            {"name": {"$regex": "^Linux|FreeBSD"}}, {"_id": 1}
        )
        oldd = [o["_id"] for o in copy.copy(old_linux_profile_id)]
        old = ", ".join(map(repr, (str(id["_id"]) for id in old_linux_profile_id)))
        print(oldd)
        new_linux_profile_id = db.noc.profiles.find_one({"name": "OS.Linux"}, {"_id": 1})
        print(new_linux_profile_id)
        self.db.execute(
            """
                          UPDATE sa_managedobject
                          SET version = null
                          WHERE profile = '%s'
                          """
            % old
        )
        self.db.execute(
            """
                          UPDATE sa_managedobject
                          SET profile = '%s'
                          WHERE profile in (%s)
                          """
            % (str(new_linux_profile_id["_id"]), old)
        )
        db.noc.actioncommands.update_many(
            {"profile": {"$in": oldd}}, {"$set": {"profile": new_linux_profile_id["_id"]}}
        )
        db.noc.firmwares.update_many(
            {"profile": {"$in": oldd}}, {"$set": {"profile": new_linux_profile_id["_id"]}}
        )
        db.noc.specs.update_many(
            {"profile": {"$in": oldd}}, {"$set": {"profile": new_linux_profile_id["_id"]}}
        )
        db.noc.profiles.remove({"name": {"$regex": "Linux."}})
