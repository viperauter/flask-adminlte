from flask_admin._compat import as_unicode
from flask_admin import Admin
from flask_security import SQLAlchemyUserDatastore
from .models import db, User, Role
from .views import AdminsView,DynamicView,DynamicMenuLink,DynamicMenuCategory
import hashlib
import urllib
from flask_admin.menu import MenuLink, MenuCategory
from flask import current_app
from flask_security import current_user
admins_store = SQLAlchemyUserDatastore(db, User, Role)


class AdminLte(Admin):
    """
    Collection of the admin views. Also manages dynamic menu structure.
    """
    def __init__(self, app=None, name=None, url=None, subdomain=None, index_view=None,
                 translations_path=None, endpoint=None, static_url_path=None, base_template=None,
                 category_icon_classes=None, short_name=None, long_name=None,
                 skin='blue'):
        super(AdminLte, self).__init__(app, name, url, subdomain, index_view, translations_path, endpoint,
                                       static_url_path, base_template, 'bootstrap4', category_icon_classes)
        self.short_name = short_name or name
        self.long_name = long_name or name
        self.skin = skin
        self.dynamic_menu_items = {}  # Dictionary to track dynamic menu items
        db.app = app
        self.add_view(AdminsView(User, db.session, name="Administrators", menu_icon_value='fa-user-secret'))

        # Register the before_request function to update dynamic menus
        if app:
            @app.before_request
            def before_request():
                self.update_all_dynamic_menus()

    def gravatar_image_url(self, email, default_url, size=96):
        return "https://www.cnavatar.com/avatar/" \
               + hashlib.md5(email.lower().encode('utf-8')).hexdigest() \
               + "?" + urllib.parse.urlencode({'d': default_url, 's': str(size)})

    def set_category_icon(self, name, icon_value, icon_type="fa"):
        cat_text = as_unicode(name)
        category = self._menu_categories.get(cat_text)

        if category is not None:
            category.icon_type = icon_type
            category.icon_value = icon_value

    def add_view(self, view):
        # Add to views
        self._views.append(view)

        # If app was provided in constructor, register view with Flask app
        if self.app is not None:
            self.app.register_blueprint(view.create_blueprint(self))

        # Only add view to menu if it's not a DynamicView
        if not isinstance(view, DynamicView):
            self._add_view_to_menu(view)

    def _track_dynamic_menu(self, view_id, item_type, *args):
        """Track dynamic menu items for a specific view"""
        if view_id not in self.dynamic_menu_items:
            self.dynamic_menu_items[view_id] = []
        self.dynamic_menu_items[view_id].append((item_type, *args))

    def add_dynamic_category(self, view_id, name, icon_type=None, icon_value=None):
        """Add a dynamic category and record it"""
        if not self._category_exists(name):
            super().add_category(name=name, icon_type=icon_type, icon_value=icon_value)
            self._track_dynamic_menu(view_id, 'category', name)

    def add_dynamic_link(self, view_id, name, url=None, category=None, icon_type=None, icon_value=None):
        """Add a dynamic link and record it"""
        # Check if the category exists; if not, create it
        if category and not self._category_exists(category):
            self.add_dynamic_category(view_id=view_id, name=category, icon_type=icon_type, icon_value=icon_value)

        # Now, check if the link exists in the specified category or globally if no category
        if not self._link_exists(name, category):
            link = MenuLink(name=name, url=url, category=category, icon_type=icon_type, icon_value=icon_value)
            super().add_link(link)
            self._track_dynamic_menu(view_id, 'link', category, name)

    def clear_dynamic_menus(self, view_id):
        """Clear dynamic menus associated with a specific view"""
        if view_id in self.dynamic_menu_items:
            for item in self.dynamic_menu_items[view_id]:
                if item[0] == 'category':
                    self._remove_category(item[1])
                elif item[0] == 'link':
                    self._remove_link(item[1], item[2])
            del self.dynamic_menu_items[view_id]  # Clean up records

    def update_all_dynamic_menus(self):
        """Update dynamic menus for all registered views"""
        for view in self._views:
            if isinstance(view, DynamicView):
                view.update_dynamic_menus()

    def _category_exists(self, name):
        """Check if a category with the given name already exists"""
        return any(category.name == name for category in self._menu_categories.values())

    def _link_exists(self, name, category=None):
        """Check if a link with the given name and category already exists"""
        if category:
            # If the link has a category, look for it in the category's items
            category_obj = self._menu_categories.get(as_unicode(category))
            if category_obj:
                return any(item.name == name for item in category_obj.get_children())
        else:
            # If there's no category, check _menu_links (uncategorized links)
            return any(link.name == name for link in self._menu_links)

    def _remove_category(self, name):
        """Remove a category by name"""
        self._menu_categories = {k: v for k, v in self._menu_categories.items() if v.name != name}
        # Also remove from _menu
        self._menu = [item for item in self._menu if not (hasattr(item, 'name') and item.name == name)]

    def _remove_link(self, name, category):
        """Remove a link by name and category"""
        if category:
            # Check in the categories
            category_obj = self._menu_categories.get(as_unicode(category))
            if category_obj:
                category_obj._children = [link for link in category_obj._children if link.name != name]
        else:
            # If no category, remove from the main _menu_links
            self._menu_links = [link for link in self._menu_links if link.name != name]
