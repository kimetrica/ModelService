import connexion
import six

from openapi_server.models.io_file import IOFile  # noqa: E501
from openapi_server.models.io_request import IORequest  # noqa: E501
from openapi_server.models.model import Model  # noqa: E501
from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.query import Query  # noqa: E501
from openapi_server.models.geo_query import GeoQuery  # noqa: E501
from openapi_server.models.text_query import TextQuery  # noqa: E501
from openapi_server.models.time_query import TimeQuery  # noqa: E501
from openapi_server import util

import requests
import configparser

import mint_client
from mint_client.rest import ApiException

# Load MINT configurations
config = configparser.ConfigParser()
config.read('config.ini')
url = config['MINT']['URL']
provenance_id = config['MINT']['PROVENANCE_ID']
username = config['MINT']['USERNAME']
password = config['MINT']['PASSWORD']

# Authenticate with MINT Model Catalog (MCAT)
configuration = mint_client.Configuration()
api_instance = mint_client.UserApi()
user = mint_client.User(username=username, password=password)

# Authenticate with MINT Data Catalog (DCAT)
resp = requests.get(f"{url}/get_session_token").json()
api_key = resp['X-Api-Key']

# Set DCAT request headers
request_headers = {
    'Content-Type': "application/json",
    'X-Api-Key': api_key
}

try:
    # Logs user into MINT
    configuration.access_token = api_instance.login_user(username, password)
    print("Log in success! Token: %s\n" % configuration.access_token)
except ApiException as e:
    print("Exception when calling UserApi->login_user: %s\n" % e)    

def list_models_post():  # noqa: E501
    """Obtain a list of current models

    Request a list of currently available models. # noqa: E501


    :rtype: List[str]
    """
    api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
    try:
        api_response = api_instance.get_models(username=username)
        models = [m.id for m in api_response]
        
        # obtain model info:
        models_infos = []
        for m in models:
            models_infos.append(model_info_model_name_get(m))
        
        return models_infos

    except ApiException as e:
        return "Exception when calling ModelApi->get_models: %s\n" % e


def model_config_model_name_get(ModelName):  # noqa: E501
    """Obtain an example model configuration.

    Submit a model name and receive a model configuration for the given model. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: ModelConfig
    """
    # get model
    try:
        api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
        model = api_instance.get_model(ModelName, username=username)
        versions = [v['id'] for v in model.has_software_version]

        # for each model version, obtain configuration ids
        configuration_ids = []
        api_instance = mint_client.ModelversionApi(mint_client.ApiClient(configuration))
        for v in versions:
            version = api_instance.get_model_version(v, username=username)
            c_ids = [c.id for c in version.has_configuration]
            configuration_ids.extend(c_ids)

        # get configurations
        configurations = []
        api_instance = mint_client.ModelconfigurationApi(mint_client.ApiClient(configuration))
        for _id in configuration_ids:
            config = api_instance.get_model_configuraton(_id, username=username)
            configurations.append({'name': ModelName, 'config': config.to_dict()})

        return configurations

    except ApiException as e:
        return "Exception when calling MINT: %s\n" % e

def model_info_model_name_get(ModelName):  # noqa: E501
    """Get basic metadata information for a specified model.

    Submit a model name and receive metadata information about the model, such as its purpose, who maintains it, and how it can be run. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: Model
    """
    return util._get_model(ModelName, configuration, username)


def model_io_post():  # noqa: E501
    """Obtain information on a given model&#39;s inputs or outputs.

    Submit a model name and receive information about the input or output files required by this model. # noqa: E501
    Note that this includes all inputs and all outputs for a given model, irrespective of the 
    configuration. In the future this could be subset to just a specific configuration.

    :param io_request: The name of a model and an IO type.
    :type io_request: dict | bytes

    :rtype: List[IOFile]
    """
    if connexion.request.is_json:
        io_request = IORequest.from_dict(connexion.request.get_json())  # noqa: E501
        name_ = io_request.name
        type_ = io_request.iotype

        try:
            # get model configuration ids
            api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
            model = api_instance.get_model(name_, username=username)
            versions = [v['id'] for v in model.has_software_version]
            

            # for each model version, obtain configuration ids
            configuration_ids = []
            api_instance = mint_client.ModelversionApi(mint_client.ApiClient(configuration))
            for v in versions:
                version = api_instance.get_model_version(v, username=username)
                c_ids = [c.id for c in version.has_configuration]
                configuration_ids.extend(c_ids)

            # get IO
            api_instance = mint_client.ModelconfigurationApi(mint_client.ApiClient(configuration))

            inputs_outputs = []
            if type_ == 'input':
                for config_id in configuration_ids:
                    response = requests.get(f"https://api.models.mint.isi.edu/v0.0.2/modelconfiguration/{config_id}/inputs?username=modelservice")
                    api_response = response.json()

                    for io in api_response:
                        io_ = util._parse_io(io, url, request_headers)
                        if io_:
                            inputs_outputs.append(io_)

            elif type_ == 'output':
                outputs = []
                for config_id in configuration_ids:
                    response = requests.get(f"https://api.models.mint.isi.edu/v0.0.2/modelconfiguration/{config_id}/outputs?username=modelservice")
                    api_response = response.json()
                    for io in api_response:
                        io_ = util._parse_io(io, url, request_headers)
                        if io_:
                            inputs_outputs.append(io_)
            return inputs_outputs

        except ApiException as e:
            return "Exception when calling MINT API: %s\n" % e


def model_parameters_model_name_post(ModelName):  # noqa: E501
    """Obtain information about a model&#39;s parameters.

    Submit a model name and receive information about the parameters used by this model. Specific parameters are used on a per-configuration basis. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: List[Parameter]
    """

    # Obtain all parameters associated with *any* configuration for 
    # the given model
    configs = model_config_model_name_get(ModelName)
    parameter_ids = set()
    for c in configs:
        for param in c['config'].get('has_parameter',[]):
            parameter_ids.add(param['id'])

    try:
        api_instance = mint_client.ParameterApi(mint_client.ApiClient(configuration))
        # List All Parameters
        api_response = api_instance.get_parameters(username=username)
        
        parameters = []
        for param in api_response:
            if param.id in parameter_ids:
                parameter = {'id': param.id,
                             'description': param.description,
                             'label': param.label,
                             # need to format the following strings as they have been converted
                             # to arrays by MINT due to duplicate entry attempts
                             'data_type': util.format_stringed_array(param.has_data_type),
                             'default_value': util.format_stringed_array(param.has_default_value)} 
                             
                             # TODO: need to implement a lookup to grab the standard name
                             # `param.type` is an array of URIs, but does not conform
                             # to how we should present `standard_name`s based on 
                             # the MaaS API spec

                             #'standard_name': param.type}
                parameters.append(parameter)
        return parameters
    except ApiException as e:
        print("Exception when calling ParameterApi->get_parameters: %s\n" % e)


def search_post():  # noqa: E501
    """Search for a model, dataset, or variable

    Search for a model, dataset, or variable based on name or standard name # noqa: E501

    :param search_item: Search parameters
    :type search_item: dict | bytes

    :rtype: SearchResult
    """
    
    if connexion.request.is_json:
        search_item = connexion.request.get_json()
        query_type = search_item['query_type']
        print(search_item)
        if query_type == 'time':
            query = TimeQuery.from_dict(search_item)
            results = util._execute_time_query(query, 
                                               url, 
                                               request_headers, 
                                               configuration,
                                               username)
            return results            
        elif query_type == 'geo':
            query = GeoQuery.from_dict(search_item)
            results = util._execute_geo_query(query, 
                                               url, 
                                               request_headers, 
                                               configuration,
                                               username)
            return results
        elif query_type == 'text':
            # TODO: incorporate model/variable search
            # this only supports text -> dataset search
            query = TextQuery.from_dict(search_item)
            results = util._execute_text_query(query, 
                                               url, 
                                               request_headers, 
                                               configuration,
                                               username)
            return results

    return [search_item]