import re
from Plugin import PluginManager


@PluginManager.registerTo("UiRequest")
class UiRequestPlugin(object):
    def __init__(self, *args, **kwargs):
        from Site import SiteManager
        self.site_manager = SiteManager.site_manager
        super(UiRequestPlugin, self).__init__(*args, **kwargs)

    # Media request

    def actionSiteMedia(self, path):
        match = re.match(
            r"/media/(?P<address>[A-Za-z0-9-]+\.[A-Za-z0-9\.-]+)(?P<inner_path>/.*|$)", path)
        if match:  # Its a valid domain, resolve first
            domain = match.group("address")
            address = self.site_manager.resolveDomain(domain)
            if address:
                path = "/media/"+address+match.group("inner_path")
        # Get the wrapper frame output
        return super(UiRequestPlugin, self).actionSiteMedia(path)

    # Is mediarequest allowed from that referer

    def isMediaRequestAllowed(self, site_address, referer):
        # Remove site address
        referer_path = re.sub(
            "http[s]{0,1}://.*?/", "/", referer).replace("/media", "")
        referer_path = re.sub(r"\?.*", "", referer_path)  # Remove http params

        if self.isProxyRequest():  # Match to site domain
            # Allow /mojo access
            referer = re.sub("^http://mojo[/]+", "http://", referer)
            referer_site_address = re.match(
                "http[s]{0,1}://(.*?)(/|$)", referer).group(1)
        else:  # Match to request path
            referer_site_address = re.match(
                r"/(?P<address>[A-Za-z0-9\.-]+)(?P<inner_path>/.*|$)", referer_path).group("address")

        if referer_site_address == site_address:  # Referer site address as simple address
            return True
        # Referer site address as dns
        elif self.site_manager.resolveDomain(referer_site_address) == site_address:
            return True
        else:  # Invalid referer
            return False
