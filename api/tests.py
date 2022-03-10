from django.test import TestCase
from api.models import SystemUser
# Create your tests here.

class UserTestCase(TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.data = [
            {
                "uid": "asudasuidsadsadsa",
                "display_name": "asdasdsa", 
                "first_name": "asdassda",
                "last_name": "Hassan",
                "email": "abc@gmail.com",
                "phone": "65446556565464",
            },
            {
                "uid": "asudasuidsadsadsaa",
                "display_name": "asdasdsa", 
                "first_name": "asad",
                "last_name": "Hassan",
                "email": "abc@gmail.com",
                "phone": "65446556565464",
            },
            {
                "uid": "asudasuidsadsaddasdsasa",
                "display_name": "asdasdsa", 
                "first_name": "Nondasade",
                "last_name": "Hassan",
                "phone": "012564465"
            },
            {
                "uid": "asudasuidsadsadasdasdsa",
                "display_name": "asdasdsa", 
                "first_name": "Sdas",
                "last_name": "Hassan",
                "email": "abcail",
                "phone": "65446556565464",
            },
            {
                "uid": "asudasuidsadsaaadsa",
                "display_name": "asdasdsa", 
                "first_name": "As",
                "last_name": "Hassan",
                "email": "abc@gmail.com",
                "phone": "54454545454",
            }
        ]


    def setUp(self):
        
        for single_user in self.data:
            new_user = SystemUser(**single_user)
            new_user.save() 

    def test_users(self):
        """Animals that can speak are correctly identified"""
        for single_user in self.data:
            user = SystemUser.objects.get(uid = single_user['uid'])
            self.assertEqual(user.uid, single_user['uid'])