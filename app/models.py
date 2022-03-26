from app import login  # , db
from flask_login import UserMixin


class User(UserMixin):  # , db.Model):
    id = 0

    def check_password(self, password):
        return True


def test(self):
    return 'Nothing'


@login.user_loader
def load_user(user_id):
    return None
    # return User.query.get(int(user_id))
