import errno
import functools
import logging
import sys
import webbrowser
import os
import click
from flask_compress import Compress
from flask_cors import CORS
from backend.server.default_config import default_config
from os import environ as env
from backend.server.app.app import Server
from backend.server.common.config.app_config import AppConfig
from flask import redirect, session, jsonify, current_app, send_file
from six.moves.urllib.parse import urlencode
from backend.common.errors import DatasetAccessError, ConfigurationError
from backend.common.utils.utils import sort_options
from flask_sock import Sock
from authlib.integrations.flask_client import OAuth
import sys
import signal
from backend.server.data_anndata.anndata_adaptor import initialize_socket
DEFAULT_CONFIG = AppConfig()
from functools import wraps
import yaml
from dotenv import load_dotenv, find_dotenv

from PIL import Image as image
from skimage import io as skiio
from skimage.transform import downscale_local_mean
import io
import numpy
from matplotlib import cm
import math
#Todo ALEJO Evitar que sea global y mantener el servidor con misma estructura de antes
tiles=[]
imin=[]
maximu=0

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

def auth0_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = 'excxg_profile' in session
        # return 401 if token is not passed
        if not token and current_app.hosted_mode:
            return jsonify({'message' : 'Authorization missing.'}), 401
  
        return  f(*args, **kwargs)
  
    return decorated


def annotation_args(func):
    @click.option(
        "--disable-annotations",
        is_flag=True,
        default=not DEFAULT_CONFIG.dataset_config.user_annotations__enable,
        show_default=True,
        help="Disable user annotation of data.",
    )
    @click.option(
        "--annotations-file",
        default=DEFAULT_CONFIG.dataset_config.user_annotations__local_file_csv__file,
        show_default=True,
        multiple=False,
        metavar="<path>",
        help="CSV file to initialize editing of existing annotations; will be altered in-place. "
        "Incompatible with --user-generated-data-dir.",
    )
    @click.option(
        "--user-generated-data-dir",
        "--annotations-dir",
        default=DEFAULT_CONFIG.dataset_config.user_annotations__local_file_csv__directory,
        show_default=False,
        multiple=False,
        metavar="<directory path>",
        help="Directory of where to save output annotations; filename will be specified in the application. "
        "Incompatible with --annotations-file and --gene-sets-file.",
    )
    @click.option(
        "--experimental-annotations-ontology",
        is_flag=True,
        default=DEFAULT_CONFIG.dataset_config.user_annotations__ontology__enable,
        show_default=True,
        help="When creating annotations, optionally autocomplete names from ontology terms.",
    )
    @click.option(
        "--experimental-annotations-ontology-obo",
        default=DEFAULT_CONFIG.dataset_config.user_annotations__ontology__obo_location,
        show_default=True,
        metavar="<path or url>",
        help="Location of OBO file defining cell annotation autosuggest terms.",
    )
    @click.option(
        "--disable-gene-sets-save",
        is_flag=True,
        default=DEFAULT_CONFIG.dataset_config.user_annotations__gene_sets__readonly,
        show_default=False,
        help="Disable saving gene sets. If disabled, users will be able to make changes to gene sets but all "
        "changes will be lost on browser refresh.",
    )
    @click.option(
        "--gene-sets-file",
        default=DEFAULT_CONFIG.dataset_config.user_annotations__local_file_csv__gene_sets_file,
        show_default=True,
        multiple=False,
        metavar="<path>",
        help="CSV file to initialize editing of gene sets; will be altered in-place. Incompatible with "
        "--user-generated-data-dir.",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def config_args(func):
    @click.option(
        "--max-category-items",
        default=DEFAULT_CONFIG.dataset_config.presentation__max_categories,
        metavar="<integer>",
        show_default=True,
        help="Will not display categories with more distinct values than specified.",
    )
    @click.option(
        "--disable-custom-colors",
        is_flag=True,
        default=False,
        show_default=False,
        help="Disable user-defined category-label colors drawn from source data file.",
    )
    @click.option(
        "--diffexp-lfc-cutoff",
        "-de",
        default=DEFAULT_CONFIG.dataset_config.diffexp__lfc_cutoff,
        show_default=True,
        metavar="<float>",
        help="Minimum log fold change threshold for differential expression.",
    )
    @click.option(
        "--disable-diffexp",
        is_flag=True,
        default=not DEFAULT_CONFIG.dataset_config.diffexp__enable,
        show_default=False,
        help="Disable on-demand differential expression.",
    )
    @click.option(
        "--embedding",
        "-e",
        default=DEFAULT_CONFIG.dataset_config.embeddings__names,
        multiple=True,
        show_default=False,
        metavar="<text>",
        help="Embedding name, eg, 'umap'. Repeat option for multiple embeddings. Defaults to all.",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def dataset_args(func):
    @click.option(
        "--obs-names",
        "-obs",
        default=DEFAULT_CONFIG.server_config.single_dataset__obs_names,
        metavar="<text>",
        help="Name of annotation field to use for observations. If not specified cellxgene will use the the obs index.",
    )
    @click.option(
        "--var-names",
        "-var",
        default=DEFAULT_CONFIG.server_config.single_dataset__var_names,
        metavar="<text>",
        help="Name of annotation to use for variables. If not specified cellxgene will use the the var index.",
    )
    @click.option(
        "--backed",
        "-b",
        is_flag=True,
        default=DEFAULT_CONFIG.server_config.adaptor__anndata_adaptor__backed,
        show_default=False,
        help="Load anndata in file-backed mode. " "This may save memory, but may result in slower overall performance.",
    )
    @click.option(
        "--title",
        "-t",
        default=DEFAULT_CONFIG.server_config.single_dataset__title,
        metavar="<text>",
        help="Title to display. If omitted will use file name.",
    )
    @click.option(
        "--about",
        default=DEFAULT_CONFIG.server_config.single_dataset__about,
        metavar="<URL>",
        help="URL providing more information about the dataset (hint: must be a fully specified absolute URL).",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def server_args(func):
    @click.option(
        "--debug",
        "-d",
        is_flag=True,
        default=DEFAULT_CONFIG.server_config.app__debug,
        show_default=True,
        help="Run in debug mode. This is helpful for cellxgene developers, "
        "or when you want more information about an error condition.",
    )
    @click.option(
        "--verbose",
        "-v",
        is_flag=True,
        default=DEFAULT_CONFIG.server_config.app__verbose,
        show_default=True,
        help="Provide verbose output, including warnings and all server requests.",
    )
    @click.option(
        "--port",
        "-p",
        metavar="<port>",
        default=DEFAULT_CONFIG.server_config.app__port,
        type=int,
        show_default=True,
        help="Port to run server on. If not specified cellxgene will find an available port.",
    )
    @click.option(
        "--host",
        metavar="<IP address>",
        default=DEFAULT_CONFIG.server_config.app__host,
        show_default=False,
        help="Host IP address. By default cellxgene will use localhost (e.g. 127.0.0.1).",
    )
    @click.option(
        "--scripts",
        "-s",
        default=DEFAULT_CONFIG.dataset_config.app__scripts,
        multiple=True,
        metavar="<text>",
        help="Additional script files to include in HTML page. If not specified, "
        "no additional script files will be included.",
        show_default=False,
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def launch_args(func):
    @annotation_args
    @config_args
    @dataset_args
    @server_args
    @click.argument("datapath", required=False, metavar="<path to data file>")
    @click.option(
        "--open",
        "-o",
        "open_browser",
        is_flag=True,
        default=DEFAULT_CONFIG.server_config.app__open_browser,
        show_default=True,
        help="Open web browser after launch.",
    )
    @click.option(
        "--config-file",
        "-c",
        "config_file",
        default=None,
        show_default=True,
        help="Location to yaml file with configuration settings",
    )
    @click.option(
        "--dump-default-config",
        "dump_default_config",
        is_flag=True,
        default=False,
        show_default=True,
        help="Print default configuration settings and exit",
    )
    @click.option(
        "--hosted",
        default=False,
        is_flag=True,
        show_default=True,
        help="Runs ExCellxgene in hosted mode.",
    ) 
    @click.option(
        "--root_embedding",
        default=None,
        show_default=True,
        help="Choose the fixed, immutable embedding. If not set, the root embedding will contain all points in the center of the screen.",
    )              
    @click.option(
        "--auth_url",
        default=None,
        show_default=True,
        help="Provide URL to use for authorization redirects.",
    )  
    @click.option(
        "--preprocess",
        default=False,
        is_flag=True,
        show_default=True,
        help="Preprocesses the input data (library size normalization and log transformation). Assumes raw input data.",
    )          
    @click.option(
        "--sam_weights",
        default=False,
        is_flag=True,
        show_default=True,
        help="Calculates SAM weights (spatial dispersions) for each gene.",
    )   
    @click.option(
        "--joint_mode",
        default=False,
        is_flag=True,
        show_default=True,
        help="Enables switching between cell and gene modes in excellxgene.",
    )                                             
    @click.help_option("--help", "-h", help="Show this message and exit.")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def handle_scripts(scripts):
    if scripts:
        click.echo(
            r"""
    / / /\ \ \__ _ _ __ _ __ (_)_ __   __ _
    \ \/  \/ / _` | '__| '_ \| | '_ \ / _` |
     \  /\  / (_| | |  | | | | | | | | (_| |
      \/  \/ \__,_|_|  |_| |_|_|_| |_|\__, |
                                      |___/
    The --scripts flag is intended for developers to include google analytics etc. You could be opening yourself to a
    security risk by including the --scripts flag. Make sure you trust the scripts that you are including.
            """
        )
        scripts_pretty = ", ".join(scripts)
        click.confirm(f"Are you sure you want to inject these scripts: {scripts_pretty}?", abort=True)


class CliLaunchServer(Server):
    """
    the CLI runs a local web server, and needs to enable a few more features.
    """

    def __init__(self, app_config):
        super().__init__(app_config)

    @staticmethod
    def _before_adding_routes(app, app_config):
        app.config["COMPRESS_MIMETYPES"] = [
            "text/html",
            "text/css",
            "text/xml",
            "application/json",
            "application/javascript",
            "application/octet-stream",
        ]
        Compress(app)
        if app_config.server_config.app__debug:
            CORS(app, supports_credentials=True)


@sort_options
@click.command(
    short_help="Launch excellxgene. " "Run `excellxgene launch --help` for more information.",
    options_metavar="<options>",
)
@launch_args
def launch(
    datapath,
    verbose,
    debug,
    open_browser,
    port,
    host,
    embedding,
    obs_names,
    var_names,
    max_category_items,
    disable_custom_colors,
    diffexp_lfc_cutoff,
    title,
    scripts,
    about,
    disable_annotations,
    annotations_file,
    user_generated_data_dir,
    gene_sets_file,
    disable_gene_sets_save,
    backed,
    disable_diffexp,
    experimental_annotations_ontology,
    experimental_annotations_ontology_obo,
    config_file,
    dump_default_config,
    hosted,
    root_embedding,
    auth_url,
    preprocess,
    sam_weights,
    joint_mode
):
    """Launch the cellxgene data viewer.
    This web app lets you explore single-cell expression data.
    Data must be in a format that cellxgene expects.
    Read the "getting started" guide to learn more:
    https://chanzuckerberg.github.io/cellxgene/getting-started.html

    Examples:

    > excellxgene launch example-dataset/pbmc3k.h5ad --title pbmc3k

    > excellxgene launch <your data file> --title <your title>

    > excellxgene launch <url>"""

    if dump_default_config:
        print(default_config)
        sys.exit(0)

    # Startup message
    click.echo("[cellxgene] Starting the CLI...")

    # app config
    app_config = AppConfig()
    app_config.root_embedding = root_embedding
    app_config.preprocess = preprocess
    app_config.sam_weights = sam_weights
    app_config.hosted_mode = hosted
    app_config.joint_mode = joint_mode
    server_config = app_config.server_config

    try:
        if config_file:
            app_config.update_from_config_file(config_file)

        # Determine which config options were give on the command line.
        # Those will override the ones provided in the config file (if provided).
        cli_config = AppConfig()
        cli_config.update_server_config(
            app__verbose=verbose,
            app__debug=debug,
            app__host=host,
            app__port=port,
            app__open_browser=open_browser,
            single_dataset__datapath=datapath,
            single_dataset__title=title,
            single_dataset__about=about,
            single_dataset__obs_names=obs_names,
            single_dataset__var_names=var_names,
            adaptor__anndata_adaptor__backed=backed,
        )
        cli_config.update_dataset_config(
            app__scripts=scripts,
            user_annotations__enable=not disable_annotations,
            user_annotations__local_file_csv__file=annotations_file,
            user_annotations__local_file_csv__directory=user_generated_data_dir,
            user_annotations__local_file_csv__gene_sets_file=gene_sets_file,
            user_annotations__gene_sets__readonly=disable_gene_sets_save,
            user_annotations__ontology__enable=experimental_annotations_ontology,
            user_annotations__ontology__obo_location=experimental_annotations_ontology_obo,
            presentation__max_categories=max_category_items,
            presentation__custom_colors=not disable_custom_colors,
            embeddings__names=embedding,
            diffexp__enable=not disable_diffexp,
            diffexp__lfc_cutoff=diffexp_lfc_cutoff,
        )

        diff = cli_config.server_config.changes_from_default()
        changes = {key: val for key, val, _ in diff}
        app_config.update_server_config(**changes)

        diff = cli_config.dataset_config.changes_from_default()
        changes = {key: val for key, val, _ in diff}
        app_config.update_dataset_config(**changes)

        # process the configuration
        #  any errors will be thrown as an exception.
        #  any info messages will be passed to the messagefn function.

        def messagefn(message):
            click.echo("[cellxgene] " + message)

        # Use a default secret if one is not provided
        if not server_config.app__flask_secret_key:
            app_config.update_server_config(app__flask_secret_key="SparkleAndShine")

        app_config.complete_config(messagefn)

    except (ConfigurationError, DatasetAccessError) as e:
        raise click.ClickException(e)

    handle_scripts(scripts)

    # create the server

    server = CliLaunchServer(app_config)
    sock = Sock(server.app)
    app_config.server_config.data_adaptor.socket = sock
    server.app.hosted_mode = hosted

    cellxgene_url = f"http://{app_config.server_config.app__host}:{app_config.server_config.app__port}"
    initialize_socket(app_config.server_config.data_adaptor)
    global in_handler
    in_handler = False
    def handler(signal, frame):
        print('\nShutting down cellxgene.')
        global in_handler
        if not in_handler:
            in_handler = True
            if hosted:
                import ray                
                ray.shutdown()        
            sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    
    if not server_config.app__verbose:
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

    if server_config.app__open_browser:
        click.echo(f"[cellxgene] Launching! Opening your browser to {cellxgene_url} now.")
        webbrowser.open(cellxgene_url)
    else:
        click.echo(f"[cellxgene] Launching! Please go to {cellxgene_url} in your browser.")

    click.echo("[cellxgene] Type CTRL-C at any time to exit.")

    image.MAX_IMAGE_PIXELS = None
    imin=[]
    imin.append(skiio.imread('images/mosaic_Cellbound3_z3-002-002.tif'))
    #imin = skiio.imread('images/dinosaur.jpg')
    partitionAmount=128
    levelsAmount=round(math.log(partitionAmount,2))
    M = imin[0].shape[0]//partitionAmount
    N = imin[0].shape[1]//partitionAmount
    tiles=[]
    tiles.append([imin[0][x:x+M,y:y+N] for x in range(0,imin[0].shape[0],M) for y in range(0,imin[0].shape[1],N)])
    maximu=imin[0].max()
    i=0
    while partitionAmount>1:
        partitionAmount=partitionAmount//2
        imin.append(downscale_local_mean(imin[i], (2,2)))
        i+=1
        M = imin[i].shape[0]//partitionAmount
        N = imin[i].shape[1]//partitionAmount
        tiles.append([imin[i][x:x+M,y:y+N] for x in range(0,imin[i].shape[0],M) for y in range(0,imin[i].shape[1],N)])
    @server.app.route("/return-files/<int:number>/<int:depth>")
    def return_files_tut(number,depth):
        try:

            tileSizeChange=tiles[levelsAmount-depth][number]
            tileSizeChange=tileSizeChange.astype(float)
            tileSizeChange=tileSizeChange/maximu
            
            imout = image.fromarray(cm.viridis(tileSizeChange, bytes=True))
            buffer = io.BytesIO()
            #First save image as in-memory.
            imout.save(buffer, "WEBP")
            buffer.seek(0)
            return send_file(buffer, mimetype='image/webp')

        except Exception as e:
            return str(e)


    if not server_config.app__verbose:
        f = open(os.devnull, "w")
        sys.stdout = f
    
    
    if hosted:
        
        oauth = OAuth(server.app)
        auth0 = oauth.register(
            'auth0',
            client_id=env.get("AUTH0_CLIENT_ID"),
            client_secret=env.get("AUTH0_CLIENT_SECRET"),
            api_base_url=f'https://{env.get("AUTH0_DOMAIN")}',
            access_token_url=f'https://{env.get("AUTH0_DOMAIN")}/oauth/token',
            authorize_url=f'https://{env.get("AUTH0_DOMAIN")}/authorize',
            client_kwargs={
                'scope': 'openid profile email',
            },
            server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
        )
        if auth_url is None:
            auth_url = cellxgene_url

        @server.app.route('/callback')
        def callback_handling():
            auth0.authorize_access_token()
            resp = auth0.get('userinfo')
            userinfo = resp.json()
            # Store the user information in flask session.
            session['jwt_payload'] = userinfo
            session['excxg_profile'] = userinfo              
            return redirect(auth_url)
        
        @server.app.route('/login')
        def login():
            return auth0.authorize_redirect(redirect_uri=auth_url+'/callback')
        
        @server.app.route('/logout')
        def logout():
            session.clear()
            params = {'returnTo': auth_url, 'client_id': env.get("AUTH0_CLIENT_ID")}
            return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

        
      
    try:
        server.app.config['SESSION_COOKIE_NAME'] = 'session_cookie'
        server.app.run(
            host=server_config.app__host,
            debug=False,
            port=server_config.app__port,
            threaded=True,
            use_debugger=False,
            use_reloader=False,
        )
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            raise click.ClickException("Port is in use, please specify an open port using the --port flag.") from e
        raise