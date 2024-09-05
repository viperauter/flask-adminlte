from adminlte.views import DynamicView
from flask_security import current_user
from sqlalchemy import func
from flask import request
from sqlalchemy import distinct
from urllib.parse import quote
from models import Document

class DocumentView(DynamicView):
    # @expose('/')
    # def index_view(self):
    #     self.update_dynamic_menus()  # Update menus before rendering the view
    #     return super().index_view()

    def update_dynamic_menus(self):
        """
        Update the dynamic menus based on user roles and projects.
        """
        # Clear existing dynamic menus specific to this view
        self.clear_dynamic_menus()

        # Determine projects based on user roles
        if "superadmin" in current_user.roles:
            projects = self.session.query(distinct(Document.project)).all()
        elif "admin" in current_user.roles:
            projects = self.session.query(distinct(Document.project)).filter(Document.owner_id == current_user.id).all()
        else:
            projects = []

        # Add category for documents
        self.add_dynamic_category(self.name, icon_value='fa-folder-open')

        # Add a link for each project
        for project in projects:
            project_name = project[0]
            encoded_project_name = quote(project_name, safe='')
            self.add_dynamic_menu_link(
                name=project_name,
                url=f'/admin/document/?project_name={encoded_project_name}',
                icon_type="fa",
                icon_value='fa-folder-open',
                category=self.name
            )

    def get_query(self):
        project_name = request.args.get('project_name')
        if current_user.is_authenticated:
            if "superadmin" in current_user.roles:
                if project_name:
                    return self.session.query(Document).filter_by(project=project_name)
                else:
                    return self.session.query(Document)
            elif "admin" in current_user.roles:
                if project_name:
                    return self.session.query(Document).filter_by(owner_id=current_user.id, project=project_name)
                else:
                    return self.session.query(Document).filter_by(owner_id=current_user.id)
        return self.session.query(Document).filter_by(id=-1)

    def get_count_query(self):
        if current_user.is_authenticated:
            if "superadmin" in current_user.roles:
                return self.session.query(func.count('*')).select_from(Document)
            elif "admin" in current_user.roles:
                return self.session.query(func.count('*')).select_from(Document).filter_by(owner_id=current_user.id)
        return self.session.query(func.count('*')).select_from(Document).filter_by(id=-1)
