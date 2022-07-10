from flask import Blueprint, render_template


class Common:
    def __init__(self):
        self.bp = Blueprint('common', __name__, url_prefix='')

        self.bp.app_errorhandler(404)(self.error_404)
        self.bp.app_errorhandler(500)(self.error_500)

        self.bp.route('/')(self.index)
        self.bp.route('/404')(self.error_404)
        self.bp.route('/500')(self.error_500)
        self.bp.route('/stream')(self.stream)

    def index(self):
        return render_template(template_name_or_list='index.html')

    def error_404(self, e=None):
        return render_template(template_name_or_list='404.html'), 404

    def error_500(self, e=None):
        return render_template(template_name_or_list='500.html'), 500

    def stream(self):
        return render_template(template_name_or_list='stream.html')
