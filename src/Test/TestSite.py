import shutil
import os

import pytest
from Site import SiteManager

TEST_DATA_PATH = "src/Test/testdata"


@pytest.mark.usefixtures("resetSettings")
class TestSite:
    def testClone(self, site):
        assert site.storage.directory == TEST_DATA_PATH + \
            "/"

        # Remove old files
        if os.path.isdir(TEST_DATA_PATH + "/"):
            shutil.rmtree(TEST_DATA_PATH +
                          "/")
        assert not os.path.isfile(
            TEST_DATA_PATH + "//content.json")

        # Clone  to
        new_site = site.clone(
            "", "", address_index=1
        )

        # Check if clone was successful
        assert new_site.address == ""
        assert new_site.storage.isFile("content.json")
        assert new_site.storage.isFile("index.html")
        assert new_site.storage.isFile("data/users/content.json")
        assert new_site.storage.isFile("data/mojoblog.db")
        assert new_site.storage.verifyFiles()["bad_files"] == [
        ]  # No bad files allowed
        assert new_site.storage.query(
            "SELECT * FROM keyvalue WHERE key = 'title'").fetchone()["value"] == "MymojoBlog"

        # Optional files should be removed

        assert len(new_site.storage.loadJson(
            "content.json").get("files_optional", {})) == 0

        # Test re-cloning (updating)

        # Changes in non-data files should be overwritten
        new_site.storage.write("index.html", b"this will be overwritten")
        assert new_site.storage.read(
            "index.html") == b"this will be overwritten"

        # Changes in data file should be kept after re-cloning
        changed_contentjson = new_site.storage.loadJson("content.json")
        changed_contentjson["description"] = "Update Description Test"
        new_site.storage.writeJson("content.json", changed_contentjson)

        changed_data = new_site.storage.loadJson("data/data.json")
        changed_data["title"] = "UpdateTest"
        new_site.storage.writeJson("data/data.json", changed_data)

        # The update should be reflected to database
        assert new_site.storage.query(
            "SELECT * FROM keyvalue WHERE key = 'title'").fetchone()["value"] == "UpdateTest"

        # Re-clone the site
        site.log.debug("Re-cloning")
        site.clone("")

        assert new_site.storage.loadJson(
            "data/data.json")["title"] == "UpdateTest"
        assert new_site.storage.loadJson("content.json")[
            "description"] == "Update Description Test"
        assert new_site.storage.read(
            "index.html") != "this will be overwritten"

        # Delete created files
        new_site.storage.deleteFiles()
        assert not os.path.isdir(
            TEST_DATA_PATH + "/")

        # Delete from site registry
        assert new_site.address in SiteManager.site_manager.sites
        SiteManager.site_manager.delete(new_site.address)
        assert new_site.address not in SiteManager.site_manager.sites
