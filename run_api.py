"""
This file is the entry point of flask api. Launch python3 ronoco_vm/run.py to run flask server
"""
import os

import requests_cache
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.debug import DebuggedApplication

os.environ['DISPLAY'] = ':0'
os.system('xhost +')


class RunAPI:
    """
    Define and setup flask server and ros topic subscriber / publisher for ronoco-vm
    """

    def __init__(self):
        """
        Launch flask server when RonocoVm is created (this constructor uses SocketIO)
        """
        self.app = None
        self.create_app()
        self.socketio = SocketIO(self.app, logger=False, cors_allowed_origins='*')
        self.setup_app()
        # self.socketio.run(host='0.0.0.0', port=8000, debug=True)
        self.socketio.run(self.app, host="0.0.0.0", debug=True)

    def create_app(self, test_config=None):
        """
        Build a Flask instance and configure it
        :param test_config: path to configuration file (Default : None)
        :return: a Flask instance
        """
        # create and configure the app
        self.app = Flask(__name__, instance_relative_config=True)
        self.app.config.from_mapping(SECRET_KEY='dev', )
        self.app.debug = True
        self.app.wsgi_app = DebuggedApplication(self.app.wsgi_app, evalex=True)
        self.app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static')

        if test_config is None:
            # load the instance config, if it exists, when not testing
            self.app.config.from_pyfile('config.py', silent=True)
        else:
            # load the test config if passed in
            self.app.config.from_mapping(test_config)

        # ensure the instance folder exists
        try:
            os.makedirs(self.app.instance_path)
        except OSError:
            pass

        def filter(response):
            # if response from gestion.eirlab.net return False
            if response.url.startswith('https://gestion.eirlab.net'):
                return False
            return True

        requests_cache.install_cache('http_cache', backend='filesystem', filter_fn=filter,
                                     expire_after=604800*2)  # exclude gestion.eirlab.net from  # cache

    def setup_app(self):
        """
        Register blueprint in app.
        The class attribute "app" must contain an Flask instance
        :return: None
        """

        import common
        self.app.register_blueprint(common.Common(self.socketio).bp)

        import member
        self.app.register_blueprint(member.Member().bp)

        import formation
        self.app.register_blueprint(formation.Formations().bp)

        import stock
        self.app.register_blueprint(stock.Stock().bp)

        CORS(self.app)


if __name__ == "__main__":
    RunAPI()
