"""Tests for the GitHub gateway."""


from hivecode.github.gateway import RepoRef, verify_webhook_signature


class TestVerifyWebhookSignature:
    def test_valid_signature(self):
        payload = b'{"action": "installed"}'
        secret = "test-secret"
        import hashlib
        import hmac

        expected = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        assert verify_webhook_signature(payload, expected, secret) is True

    def test_invalid_signature(self):
        payload = b'{"action": "installed"}'
        secret = "test-secret"
        wrong_signature = "sha256=invalid"

        assert verify_webhook_signature(payload, wrong_signature, secret) is False

    def test_tampered_payload(self):
        payload = b'{"action": "installed"}'
        secret = "test-secret"
        import hashlib
        import hmac

        expected = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        tampered = b'{"action": "deleted"}'
        assert verify_webhook_signature(tampered, expected, secret) is False


class TestRepoRef:
    def test_full_name(self):
        repo = RepoRef(owner="octocat", repo="hello-world")
        assert repo.full_name == "octocat/hello-world"
