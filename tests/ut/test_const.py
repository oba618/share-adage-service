

class TestConst:

    def test_send_reason(self):

        from common.const import SendReason

        obj = SendReason.REGISTRATION_USER

        assert obj.value == 100
        assert obj.point == 100
        assert obj.message == 'ユーザー登録ありがとうございます！'

        obj = SendReason(100)

        assert obj.message == 'ユーザー登録ありがとうございます！'
