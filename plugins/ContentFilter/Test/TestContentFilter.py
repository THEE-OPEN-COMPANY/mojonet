import pytest
from ContentFilter import ContentFilterPlugin
from Site import SiteManager


@pytest.fixture
def filter_storage():
    ContentFilterPlugin.filter_storage = ContentFilterPlugin.ContentFilterStorage(
        SiteManager.site_manager)
    return ContentFilterPlugin.filter_storage


@pytest.mark.usefixtures("resetSettings")
@pytest.mark.usefixtures("resetTempSettings")
class TestContentFilter:
    def createInclude(self, site):
        site.storage.writeJson("filters.json", {
            "mutes": {"": {}},
            "siteblocks": {site.address: {}}
        })

    def testIncludeLoad(self, site, filter_storage):
        self.createInclude(site)
        filter_storage.file_content["includes"]["%s/%s" % (site.address, "filters.json")] = {
            "date_added": 1528295893,
        }

        assert not filter_storage.include_filters["mutes"]
        assert not filter_storage.isMuted("")
        assert not filter_storage.isSiteblocked(site.address)
        filter_storage.includeUpdateAll(update_site_dbs=False)
        assert len(filter_storage.include_filters["mutes"]) == 1
        assert filter_storage.isMuted("")
        assert filter_storage.isSiteblocked(site.address)

    def testIncludeAdd(self, site, filter_storage):
        self.createInclude(site)
        query_num_json = "SELECT COUNT(*) AS num FROM json WHERE directory = 'users/'"
        assert not filter_storage.isSiteblocked(site.address)
        assert not filter_storage.isMuted("")
        assert site.storage.query(query_num_json).fetchone()["num"] == 2

        # Add include
        filter_storage.includeAdd(site.address, "filters.json")

        assert filter_storage.isSiteblocked(site.address)
        assert filter_storage.isMuted("")
        assert site.storage.query(query_num_json).fetchone()["num"] == 0

        # Remove include
        filter_storage.includeRemove(site.address, "filters.json")

        assert not filter_storage.isSiteblocked(site.address)
        assert not filter_storage.isMuted("")
        assert site.storage.query(query_num_json).fetchone()["num"] == 2

    def testIncludeChange(self, site, filter_storage):
        self.createInclude(site)
        filter_storage.includeAdd(site.address, "filters.json")
        assert filter_storage.isSiteblocked(site.address)
        assert filter_storage.isMuted("")

        # Add new blocked site
        assert not filter_storage.isSiteblocked("1Hello")

        filter_content = site.storage.loadJson("filters.json")
        filter_content["siteblocks"]["1Hello"] = {}
        site.storage.writeJson("filters.json", filter_content)

        assert filter_storage.isSiteblocked("1Hello")

        # Add new muted user
        query_num_json = "SELECT COUNT(*) AS num FROM json WHERE directory = 'users/'"
        assert not filter_storage.isMuted("")
        assert site.storage.query(query_num_json).fetchone()["num"] == 2

        filter_content["mutes"][""] = {}
        site.storage.writeJson("filters.json", filter_content)

        assert filter_storage.isMuted("")
        assert site.storage.query(query_num_json).fetchone()["num"] == 0
