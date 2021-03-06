import json
import io

import pytest

from Crypt import CryptBitcoin
from Content.ContentManager import VerifyError, SignError


@pytest.mark.usefixtures("resetSettings")
class TestContentUser:
    def testSigners(self, site):
        # File info for not existing user file
        file_info = site.content_manager.getFileInfo(
            "data/users/notexist/data.json")
        assert file_info["content_inner_path"] == "data/users/notexist/content.json"
        file_info = site.content_manager.getFileInfo(
            "data/users/notexist/a/b/data.json")
        assert file_info["content_inner_path"] == "data/users/notexist/content.json"
        valid_signers = site.content_manager.getValidSigners(
            "data/users/notexist/content.json")
        assert valid_signers == [
            "14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet", "notexist", ""]

        # File info for exsitsing user file
        valid_signers = site.content_manager.getValidSigners(
            "data/users//content.json")
        assert '' in valid_signers  # The site address
        # Admin user defined in data/users/content.json
        assert '14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet' in valid_signers
        assert '' in valid_signers  # The user itself
        assert len(valid_signers) == 3  # No more valid signers

        # Valid signer for banned user
        user_content = site.storage.loadJson(
            "data/users//content.json")
        user_content["cert_user_id"] = "bad@mojoid.bit"

        valid_signers = site.content_manager.getValidSigners(
            "data/users//content.json", user_content)
        assert '' in valid_signers  # The site address
        # Admin user defined in data/users/content.json
        assert '14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet' in valid_signers
        assert '' not in valid_signers  # The user itself

    def testRules(self, site):
        # We going to manipulate it this test rules based on data/users/content.json
        user_content = site.storage.loadJson(
            "data/users//content.json")

        # Known user
        user_content["cert_auth_type"] = "web"
        user_content["cert_user_id"] = "nofish@mojoid.bit"
        rules = site.content_manager.getRules(
            "data/users//content.json", user_content)
        assert rules["max_size"] == 100000
        assert "" in rules["signers"]

        # Unknown user
        user_content["cert_auth_type"] = "web"
        user_content["cert_user_id"] = "noone@mojoid.bit"
        rules = site.content_manager.getRules(
            "data/users//content.json", user_content)
        assert rules["max_size"] == 10000
        assert "" in rules["signers"]

        # User with more size limit based on auth type
        user_content["cert_auth_type"] = "bitmsg"
        user_content["cert_user_id"] = "noone@mojoid.bit"
        rules = site.content_manager.getRules(
            "data/users//content.json", user_content)
        assert rules["max_size"] == 15000
        assert "" in rules["signers"]

        # Banned user
        user_content["cert_auth_type"] = "web"
        user_content["cert_user_id"] = "bad@mojoid.bit"
        rules = site.content_manager.getRules(
            "data/users//content.json", user_content)
        assert "" not in rules["signers"]

    def testRulesAddress(self, site):
        user_inner_path = "data/users//content.json"
        user_content = site.storage.loadJson(user_inner_path)

        rules = site.content_manager.getRules(user_inner_path, user_content)
        assert rules["max_size"] == 10000
        assert "" in rules["signers"]

        users_content = site.content_manager.contents["data/users/content.json"]

        # Ban user based on address
        users_content["user_contents"]["permissions"][""] = False
        rules = site.content_manager.getRules(user_inner_path, user_content)
        assert "" not in rules["signers"]

        # Change max allowed size
        users_content["user_contents"]["permissions"][""] = {
            "max_size": 20000}
        rules = site.content_manager.getRules(user_inner_path, user_content)
        assert rules["max_size"] == 20000

    def testVerifyAddress(self, site):
        # For
        privatekey = ""
        user_inner_path = "data/users//content.json"
        data_dict = site.storage.loadJson(user_inner_path)
        users_content = site.content_manager.contents["data/users/content.json"]

        data = io.BytesIO(json.dumps(data_dict).encode())
        assert site.content_manager.verifyFile(
            user_inner_path, data, ignore_same=False)

        # Test error on 15k data.json
        data_dict["files"]["data.json"]["size"] = 1024 * 15
        del data_dict["signs"]  # Remove signs before signing
        data_dict["signs"] = {
            "": CryptBitcoin.sign(json.dumps(data_dict, sort_keys=True), privatekey)
        }
        data = io.BytesIO(json.dumps(data_dict).encode())
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                user_inner_path, data, ignore_same=False)
        assert "Include too large" in str(err.value)

        # Give more space based on address
        users_content["user_contents"]["permissions"][""] = {
            "max_size": 20000}
        del data_dict["signs"]  # Remove signs before signing
        data_dict["signs"] = {
            "": CryptBitcoin.sign(json.dumps(data_dict, sort_keys=True), privatekey)
        }
        data = io.BytesIO(json.dumps(data_dict).encode())
        assert site.content_manager.verifyFile(
            user_inner_path, data, ignore_same=False)

    def testVerify(self, site):
        # For
        privatekey = ""
        user_inner_path = "data/users//content.json"
        data_dict = site.storage.loadJson(user_inner_path)
        users_content = site.content_manager.contents["data/users/content.json"]

        data = io.BytesIO(json.dumps(data_dict).encode())
        assert site.content_manager.verifyFile(
            user_inner_path, data, ignore_same=False)

        # Test max size exception by setting allowed to 0
        rules = site.content_manager.getRules(user_inner_path, data_dict)
        assert rules["max_size"] == 10000
        assert users_content["user_contents"]["permission_rules"][".*"]["max_size"] == 10000

        users_content["user_contents"]["permission_rules"][".*"]["max_size"] = 0
        rules = site.content_manager.getRules(user_inner_path, data_dict)
        assert rules["max_size"] == 0
        data = io.BytesIO(json.dumps(data_dict).encode())

        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                user_inner_path, data, ignore_same=False)
        assert "Include too large" in str(err.value)
        # Reset
        users_content["user_contents"]["permission_rules"][".*"]["max_size"] = 10000

        # Test max optional size exception
        # 1 MB gif = Allowed
        data_dict["files_optional"]["peanut-butter-jelly-time.gif"]["size"] = 1024 * 1024
        del data_dict["signs"]  # Remove signs before signing
        data_dict["signs"] = {
            "": CryptBitcoin.sign(json.dumps(data_dict, sort_keys=True), privatekey)
        }
        data = io.BytesIO(json.dumps(data_dict).encode())
        assert site.content_manager.verifyFile(
            user_inner_path, data, ignore_same=False)

        # 100 MB gif = Not allowed
        data_dict["files_optional"]["peanut-butter-jelly-time.gif"]["size"] = 100 * 1024 * 1024
        del data_dict["signs"]  # Remove signs before signing
        data_dict["signs"] = {
            "": CryptBitcoin.sign(json.dumps(data_dict, sort_keys=True), privatekey)
        }
        data = io.BytesIO(json.dumps(data_dict).encode())
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                user_inner_path, data, ignore_same=False)
        assert "Include optional files too large" in str(err.value)
        # Reset
        data_dict["files_optional"]["peanut-butter-jelly-time.gif"]["size"] = 1024 * 1024

        # hello.exe = Not allowed
        data_dict["files_optional"]["hello.exe"] = data_dict["files_optional"]["peanut-butter-jelly-time.gif"]
        del data_dict["signs"]  # Remove signs before signing
        data_dict["signs"] = {
            "": CryptBitcoin.sign(json.dumps(data_dict, sort_keys=True), privatekey)
        }
        data = io.BytesIO(json.dumps(data_dict).encode())
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                user_inner_path, data, ignore_same=False)
        assert "Optional file not allowed" in str(err.value)
        del data_dict["files_optional"]["hello.exe"]  # Reset

        # Includes not allowed in user content
        data_dict["includes"] = {"other.json": {}}
        del data_dict["signs"]  # Remove signs before signing
        data_dict["signs"] = {
            "": CryptBitcoin.sign(json.dumps(data_dict, sort_keys=True), privatekey)
        }
        data = io.BytesIO(json.dumps(data_dict).encode())
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                user_inner_path, data, ignore_same=False)
        assert "Includes not allowed" in str(err.value)

    def testCert(self, site):
        # user_addr = ""
        user_priv = "5Kk7FSA63FC2ViKmKLuBxk9gQkaQ5713hKq8LmFAf4cVeXh6K6A"
        # cert_addr = "14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet"
        cert_priv = "5JusJDSjHaMHwUjDT3o6eQ54pA6poo8La5fAgn1wNc3iK59jxjA"

        # Check if the user file is loaded
        assert "data/users//content.json" in site.content_manager.contents
        user_content = site.content_manager.contents["data/users//content.json"]
        rules_content = site.content_manager.contents["data/users/content.json"]

        # Override valid cert signers for the test
        rules_content["user_contents"]["cert_signers"]["mojoid.bit"] = [
            "14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet",
            "1iD5ZQJMNXu43w1qLB8sfdHVKppVMduGz"
        ]

        # Check valid cert signers
        rules = site.content_manager.getRules(
            "data/users//content.json", user_content)
        assert rules["cert_signers"] == {"mojoid.bit": [
            "14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet",
            "1iD5ZQJMNXu43w1qLB8sfdHVKppVMduGz"
        ]}

        # Sign a valid cert
        user_content["cert_sign"] = CryptBitcoin.sign("#%s/%s" % (
            user_content["cert_auth_type"],
            user_content["cert_user_id"].split("@")[0]
        ), cert_priv)

        # Verify cert
        assert site.content_manager.verifyCert(
            "data/users//content.json", user_content)

        # Verify if the cert is valid for other address
        assert not site.content_manager.verifyCert(
            "data/users/badaddress/content.json", user_content)

        # Sign user content
        signed_content = site.content_manager.sign(
            "data/users//content.json", user_priv, filewrite=False
        )

        # Test user cert
        assert site.content_manager.verifyFile(
            "data/users//content.json",
            io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
        )

        # Test banned user
        cert_user_id = user_content["cert_user_id"]  # My username
        site.content_manager.contents["data/users/content.json"]["user_contents"]["permissions"][cert_user_id] = False
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                "data/users//content.json",
                io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
            )
        assert "Valid signs: 0/1" in str(err.value)
        # Reset
        del site.content_manager.contents["data/users/content.json"]["user_contents"]["permissions"][cert_user_id]

        # Test invalid cert
        user_content["cert_sign"] = CryptBitcoin.sign(
            "badaddress#%s/%s" % (user_content["cert_auth_type"],
                                  user_content["cert_user_id"]), cert_priv
        )
        signed_content = site.content_manager.sign(
            "data/users//content.json", user_priv, filewrite=False
        )
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                "data/users//content.json",
                io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
            )
        assert "Invalid cert" in str(err.value)

        # Test banned user, signed by the site owner
        user_content["cert_sign"] = CryptBitcoin.sign("#%s/%s" % (
            user_content["cert_auth_type"],
            user_content["cert_user_id"].split("@")[0]
        ), cert_priv)
        cert_user_id = user_content["cert_user_id"]  # My username
        site.content_manager.contents["data/users/content.json"]["user_contents"]["permissions"][cert_user_id] = False

        # For
        site_privatekey = ""
        del user_content["signs"]  # Remove signs before signing
        user_content["signs"] = {
            "": CryptBitcoin.sign(json.dumps(user_content, sort_keys=True), site_privatekey)
        }
        assert site.content_manager.verifyFile(
            "data/users//content.json",
            io.BytesIO(json.dumps(user_content).encode()), ignore_same=False
        )

    def testMissingCert(self, site):
        user_priv = "5Kk7FSA63FC2ViKmKLuBxk9gQkaQ5713hKq8LmFAf4cVeXh6K6A"
        cert_priv = "5JusJDSjHaMHwUjDT3o6eQ54pA6poo8La5fAgn1wNc3iK59jxjA"

        user_content = site.content_manager.contents["data/users//content.json"]
        rules_content = site.content_manager.contents["data/users/content.json"]

        # Override valid cert signers for the test
        rules_content["user_contents"]["cert_signers"]["mojoid.bit"] = [
            "14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet",
            "1iD5ZQJMNXu43w1qLB8sfdHVKppVMduGz"
        ]

        # Sign a valid cert
        user_content["cert_sign"] = CryptBitcoin.sign("#%s/%s" % (
            user_content["cert_auth_type"],
            user_content["cert_user_id"].split("@")[0]
        ), cert_priv)
        signed_content = site.content_manager.sign(
            "data/users//content.json", user_priv, filewrite=False
        )

        assert site.content_manager.verifyFile(
            "data/users//content.json",
            io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
        )

        # Test invalid cert_user_id
        user_content["cert_user_id"] = "nodomain"
        user_content["signs"] = {
            "": CryptBitcoin.sign(json.dumps(user_content, sort_keys=True), user_priv)
        }
        signed_content = site.content_manager.sign(
            "data/users//content.json", user_priv, filewrite=False
        )
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                "data/users//content.json",
                io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
            )
        assert "Invalid domain in cert_user_id" in str(err.value)

        # Test removed cert
        del user_content["cert_user_id"]
        del user_content["cert_auth_type"]
        del user_content["signs"]  # Remove signs before signing
        user_content["signs"] = {
            "": CryptBitcoin.sign(json.dumps(user_content, sort_keys=True), user_priv)
        }
        signed_content = site.content_manager.sign(
            "data/users//content.json", user_priv, filewrite=False
        )
        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                "data/users//content.json",
                io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
            )
        assert "Missing cert_user_id" in str(err.value)

    def testCertSignersPattern(self, site):
        user_priv = "5Kk7FSA63FC2ViKmKLuBxk9gQkaQ5713hKq8LmFAf4cVeXh6K6A"
        # For 14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet
        cert_priv = "5JusJDSjHaMHwUjDT3o6eQ54pA6poo8La5fAgn1wNc3iK59jxjA"

        user_content = site.content_manager.contents["data/users//content.json"]
        rules_content = site.content_manager.contents["data/users/content.json"]

        # Override valid cert signers for the test
        rules_content["user_contents"]["cert_signers_pattern"] = "14wgQ[0-9][A-Z]"

        # Sign a valid cert
        user_content["cert_user_id"] = "certuser@14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet"
        user_content["cert_sign"] = CryptBitcoin.sign("#%s/%s" % (
            user_content["cert_auth_type"],
            "certuser"
        ), cert_priv)
        signed_content = site.content_manager.sign(
            "data/users//content.json", user_priv, filewrite=False
        )

        assert site.content_manager.verifyFile(
            "data/users//content.json",
            io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
        )

        # Cert does not matches the pattern
        rules_content["user_contents"]["cert_signers_pattern"] = "14wgX[0-9][A-Z]"

        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                "data/users//content.json",
                io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
            )
        assert "Invalid cert signer: 14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet" in str(
            err.value)

        # Removed cert_signers_pattern
        del rules_content["user_contents"]["cert_signers_pattern"]

        with pytest.raises(VerifyError) as err:
            site.content_manager.verifyFile(
                "data/users//content.json",
                io.BytesIO(json.dumps(signed_content).encode()), ignore_same=False
            )
        assert "Invalid cert signer: 14wgQ4VDDZNoRMFF4yCDuTrBSHmYhL3bet" in str(
            err.value)

    def testNewFile(self, site):
        # For
        privatekey = ""
        inner_path = "data/users/1NEWrZMkarjVg5ax9W4qThir3BFUikbW6C/content.json"

        site.storage.writeJson(inner_path, {"test": "data"})
        site.content_manager.sign(inner_path, privatekey)
        assert "test" in site.storage.loadJson(inner_path)

        site.storage.delete(inner_path)
