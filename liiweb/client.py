import logging
import requests


log = logging.getLogger(__name__)

JSON_CONTENT_TYPE = 'application/vnd.api+json'


class LIIWebClient:
    """ A client for the LIIWeb JSON API that makes it easier to work with content in LIIWeb.
    """
    def __init__(self, url, username, password):
        """
        Create a new client.

        :param url: LII URL
        :param username: LII API user username
        :param password: LII API user password
        """
        self.session = requests.session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'Accept': JSON_CONTENT_TYPE,
        })
        self.url = url

    def find_legislation(self, frbr_uri_prefix, fields=('field_frbr_uri',)):
        """ Fetch a single legislation expression, if it exists, by filtering on the FRBR URI.
        We do this because there is no GET endpoint for a work FRBR URI, only an expression FRBR URI.

        By default, only fetches the id and frbr_uri fields. Specify a list of fields to fetch otherwise.

        :param frbr_uri_prefix: legislation FRBR URI.
        :param fields: a tuple of fields to fetch, in addition to the node id.
        """
        params = {
            'filter[field_frbr_uri][value]': frbr_uri_prefix,
            'filter[field_frbr_uri][operator]': 'STARTS_WITH'
        }

        if fields:
            params['fields[node--legislation]'] = ','.join(fields)

        resp = self.session.get(self.url + '/jsonapi/node/legislation', params=params)
        resp.raise_for_status()
        info = resp.json()
        if info['data']:
            return info['data'][0]

    def get_legislation(self, expr_uri, fields=('field_frbr_uri',)):
        """ Fetch a single legislation expression, if it exists.

        By default, only fetches the id and frbr_uri fields. Specify a list of fields to fetch otherwise.

        :param expr_uri: legislation FRBR URI.
        :param fields: a tuple of fields to fetch, in addition to the node id.
        """
        # the GET request requires this accept header, not the default one
        headers = {
            'Accept': 'application/json',
        }
        params = {}
        if fields:
            params['fields[node--legislation]'] = ','.join(fields)

        resp = self.session.get(self.url + expr_uri, params=params, headers=headers)
        if resp.status_code == 404:
            return
        resp.raise_for_status()
        info = resp.json()
        if info['data']:
            return info['data']

    def list_legislation(self, place_code):
        """ List all legislation expressions for a place.

        :param place_code: country code such as 'za' or country and locality such as 'za-cpt'.
        """
        results = []
        params = {
            'filter[field_frbr_uri][value]': f'/akn/{place_code}/',
            'filter[field_frbr_uri][operator]': 'STARTS_WITH',
            'fields[node--legislation]': 'field_frbr_uri',
        }
        url = self.url + '/jsonapi/node/legislation'
        while url:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            info = resp.json()
            results.extend(info['data'])
            # pagination
            url = info['links'].get('next', {}).get('href')
            if url and url.startswith('http://'):
                url = 'https://' + url[7:]
            # clear these, they're baked into the url now
            params = {}

        return results

    def create_legislation_work(self, info):
        """ Create a new legislation work and expression and return the full description.

        :param info: full description of the legislation, in Drupal JSON format
        """
        resp = self.session.post(
            self.url + '/jsonapi/node/legislation',
            json=info,
            headers={'Content-Type': JSON_CONTENT_TYPE})
        if resp.status_code >= 400:
            log.error(f"Error from lii: {resp.text}")
        resp.raise_for_status()
        return resp.json()['data']

    def create_legislation(self, expr_uri, info):
        """ Create a new legislation expression and return the full description.

        :param expr_uri: expression URI
        :param info: full description of the legislation, in Drupal JSON format
        """
        resp = self.session.post(
            self.url + expr_uri,
            json=info,
            headers={'Content-Type': JSON_CONTENT_TYPE})
        if resp.status_code >= 400:
            log.error(f"Error from lii: {resp.text}")
        resp.raise_for_status()
        return resp.json()['data']

    def delete_legislation(self, expr_uri):
        """ Delete legislation by node id.

        :param nid: legislation node id to delete
        """
        resp = self.session.delete(self.url + expr_uri)
        resp.raise_for_status()

    def update_legislation(self, expr_uri, info):
        """ Patch an existing legislation by node id.

        :param expr_uri: expression FRBR URI
        :param info: updated information, in Drupal JSON format
        """
        resp = self.session.patch(
            self.url + expr_uri,
            json=info,
            headers={'Content-Type': JSON_CONTENT_TYPE})
        resp.raise_for_status()
        return resp.json()['data']

    def upload_file(self, node, fname, data, fieldname):
        """ Upload a file to the lii and return the node id.

        :param node: node type, such as 'legislation'
        :param fname: filename to use
        :param data: contents of the file as a bytestring
        :param fieldname: name of the field on the node

        :returns: the id of the uploaded file
        """
        resp = self.session.post(
            self.url + f'/jsonapi/node/{node}/{fieldname}',
            data=data,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename="{fname}"',
            }
        )
        if resp.status_code >= 400:
            log.error(f"Error from lii: {resp.text}")
        resp.raise_for_status()
        return resp.json()['data']['id']

    def list_legislation_files(self, nid, field):
        """ List files associated with a legislation node.

        :param nid: legislation node id
        :param field: file type to list, either 'field_images' or 'field_files'
        """
        resp = self.session.get(self.url + f"/jsonapi/node/legislation/{nid}/{field}")
        resp.raise_for_status()
        return resp.json()['data']
