from flask import Flask, redirect, url_for
from flask_migrate import Migrate
from flask_security import Security, current_user
from flask_security.utils import hash_password
from flask_admin import helpers as admin_helpers
from adminlte.admin import AdminLte, admins_store, db
from adminlte.models import Role
from models import db
from models.document import Document
from views.document import DocumentView
from flask_security.signals import user_registered
from adminlte.views import ExtendedRegisterForm


app = Flask(__name__)
app.config.from_pyfile('config.py')

db.init_app(app)
db.app = app

migrate = Migrate(app, db)

admin_migrate = Migrate(app, db)

security = Security(app, admins_store,register_form=ExtendedRegisterForm)

admin = AdminLte(app, skin = 'blue-light', name = 'FKDoc', short_name = "<b>Doc</b>", long_name = "<b>FKDoc</b>")

admin.add_view(DocumentView(Document, db.session, name = "Documents", menu_icon_value = 'fa-folder-open'))

@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template = admin.base_template,
        admin_view = admin.index_view,
        h = admin_helpers,
        get_url = url_for
    )

@user_registered.connect_via(app)
def assign_default_role(app, user, confirm_token):
    default_role = Role.query.filter_by(name="admin").first()
    if not default_role:
        default_role = Role(name="admin")
        db.session.add(default_role)
        db.session.commit()

    user.roles.append(default_role)
    db.session.add(default_role)

    print("received registered user signal", default_role)

@app.route('/')
def index():
    if not current_user:
        return redirect("/admin/login")
    return redirect("/admin")

@app.cli.command('build_sample_db')
def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    db.drop_all()
    db.create_all()

    with app.app_context():
        super_admin_role = Role(name = 'superadmin')
        admin_role = Role(name = 'admin')
        db.session.add(super_admin_role)
        db.session.add(admin_role)
        db.session.commit()

        test_user = admins_store.create_user(
            first_name = 'John',
            last_name = 'Doe',
            email = 'admin@admin.com',
            password = hash_password('admin'),
            roles = [super_admin_role, admin_role]
        )
        db.session.add(test_user)
        db.session.commit()
    return

# from flask_debugtoolbar import DebugToolbarExtension
# app.debug = True
# toolbar = DebugToolbarExtension(app)


if __name__ == '__main__':
    app.run()
