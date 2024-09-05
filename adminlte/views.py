from flask_admin.contrib import sqla
from flask_security import current_user,RegisterForm
from flask import url_for, redirect, request, abort,current_app
from flask_admin import menu
from wtforms import StringField
from wtforms.validators import DataRequired
from flask_admin.menu import MenuLink, MenuCategory
import uuid
from urllib.parse import quote
from flask_admin import expose

class FaLink(menu.MenuLink):

    def __init__(self, name, url = None, endpoint = None, category = None, class_name = None, icon_type = "fa",
                 icon_value = None, target = None):
        super(FaLink, self).__init__(name, url, endpoint, category, class_name, icon_type, icon_value, target)


class FaModelView(sqla.ModelView):

    def __init__(self, model, session, name = None, category = None, endpoint = None, url = None, static_folder = None,
                 menu_class_name = None, menu_icon_type = "fa", menu_icon_value = None):
        super(FaModelView, self).__init__(model, session, name, category, endpoint, url, static_folder, menu_class_name,
                                          menu_icon_type, menu_icon_value)


class BaseAdminView(FaModelView):
    required_role = 'admin'
    can_export = True
    can_view_details = True
    can_create = True
    can_edit = True
    can_delete = True
    edit_modal = True
    create_modal = True
    details_modal = True

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role(self.required_role):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for('security.login', next = request.url))


class AdminsView(BaseAdminView):
    required_role = 'superadmin'
    column_display_all_relations = True
    column_editable_list = ['email', 'first_name', 'last_name']
    column_searchable_list = ['roles.name', 'email', 'first_name', 'last_name']
    column_exclude_list = ['password']
    column_details_exclude_list = ['password']
    column_filters = ['email', 'first_name', 'last_name']
    can_export = True
    can_view_details = True
    can_create = True
    can_edit = True
    can_delete = True
    edit_modal = True
    create_modal = True
    details_modal = True

class ExtendedRegisterForm(RegisterForm):
    first_name = StringField('First Name', [DataRequired()])
    last_name = StringField('Last Name', [DataRequired()])

class DynamicMenuLink(MenuLink):
    def __init__(self, *args, **kwargs):
        self._uuid = uuid.uuid4()
        super().__init__( *args, **kwargs)

class DynamicMenuCategory(MenuCategory):
    def __init__(self, *args, **kwargs):
        self._uuid = uuid.uuid4()
        super().__init__( *args, **kwargs)


class DynamicView(BaseAdminView):
    def __init__(self, *args, **kwargs):
        super(DynamicView, self).__init__(*args, **kwargs)
        self.view_id = f"{self.__class__.__name__}_{str(uuid.uuid4())}"  # Generate a unique UUID for each view instance

    def get_view_id(self):
        """Return the unique view ID"""
        return self.view_id

    def _get_adminlte(self):
        """Retrieve the Admin instance from the Flask app context"""
        with current_app.app_context():
            adminlte = current_app.extensions['admin'][0]
        return adminlte

    def update_dynamic_menus(self):
        """
        Method to update dynamic menus. Should be overridden by subclasses to define specific menu logic.
        """
        raise NotImplementedError("Subclasses should implement this method to update dynamic menus.")

    def add_dynamic_category(self, name, icon_type="fa", icon_value=None):
        """Add a dynamic category using the AdminLte API"""
        admin = self._get_adminlte()
        admin.add_dynamic_category(self.get_view_id(), name, icon_type, icon_value)

    def add_dynamic_menu_link(self, name, url=None, category=None, icon_type="fa", icon_value=None):
        """Add a dynamic menu link using the AdminLte API"""
        admin = self._get_adminlte()
        admin.add_dynamic_link(self.get_view_id(), name, url, category, icon_type, icon_value)

    def clear_dynamic_menus(self):
        """Clear dynamic menus associated with this view"""
        admin = self._get_adminlte()
        admin.clear_dynamic_menus(self.get_view_id())
