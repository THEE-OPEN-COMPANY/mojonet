import pytest

from Crypt import CryptBitcoin


@pytest.mark.usefixtures("resetSettings")
class TestUser:
    def testAddress(self, user):
        assert user.master_address == ""
        address_index = 1458664252141532163166741013621928587528255888800826689784628722366466547364755811
        assert user.getAddressAuthIndex(
            "") == address_index

    # Re-generate privatekey based on address_index
    def testNewSite(self, user):
        address, address_index, site_data = user.getNewSiteData()  # Create a new random site
        assert CryptBitcoin.hdPrivatekey(
            user.master_seed, address_index) == site_data["privatekey"]

        user.sites = {}  # Reset user data

        # Site address and auth address is different
        assert user.getSiteData(address)["auth_address"] != address
        # Re-generate auth_privatekey for site
        assert user.getSiteData(
            address)["auth_privatekey"] == site_data["auth_privatekey"]

    def testAuthAddress(self, user):
        # Auth address without Cert
        auth_address = user.getAuthAddress(
            "")
        assert auth_address == ""
        auth_privatekey = user.getAuthPrivatekey(
            "")
        assert CryptBitcoin.privatekeyToAddress(
            auth_privatekey) == auth_address

    def testCert(self, user):
        cert_auth_address = user.getAuthAddress(
            "")  # Add site to user's registry
        # Add cert
        user.addCert(cert_auth_address, "mojoid.bit",
                     "faketype", "fakeuser", "fakesign")
        user.setCert("", "mojoid.bit")

        # By using certificate the auth address should be same as the certificate provider
        assert user.getAuthAddress(
            "") == cert_auth_address
        auth_privatekey = user.getAuthPrivatekey(
            "")
        assert CryptBitcoin.privatekeyToAddress(
            auth_privatekey) == cert_auth_address

        # Test delete site data
        assert "" in user.sites
        user.deleteSiteData("")
        assert "" not in user.sites

        # Re-create add site should generate normal, unique auth_address
        assert not user.getAuthAddress(
            "") == cert_auth_address
        assert user.getAuthAddress(
            "") == ""
