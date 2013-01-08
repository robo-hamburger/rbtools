from optparse import make_option

from rbtools.api.errors import APIError
from rbtools.commands import Command
from rbtools.utils.process import die


SUBMITTED = 'submitted'
DISCARDED = 'discarded'


class Close(Command):
    """Close a specific review request as discarded or submitted.

    By default, the command will change the status to submitted. The
    user can provide an optional description for this action.
    """
    name = "close"
    author = "John Sintal"
    option_list = [
        make_option("--close_type",
                    dest="close_type",
                    default=SUBMITTED,
                    help="either submitted or discarded"),
        make_option("--description",
                    dest="description",
                    default=None,
                    help="optional description accompanied with change"),
        make_option("--server",
                    dest="server",
                    metavar="SERVER",
                    help="specify a different Review Board server to use"),
        make_option("-d", "--debug",
                    action="store_true",
                    dest="debug",
                    help="display debug output"),
    ]

    def __init__(self):
        super(Close, self).__init__()
        self.option_defaults = {
            'server': self.config.get('REVIEWBOARD_URL', None),
            'username': self.config.get('USERNAME', None),
            'password': self.config.get('PASSWORD', None),
            'debug': self.config.get('DEBUG', False),
        }

    def get_review_request(self, request_id):
        """Return the review request resource for the given ID."""
        try:
            request = \
                self.root_resource.get_review_requests().get_item(request_id)
        except APIError, e:
            die("Error getting review request: %s" % (e))

        return request

    def check_valid_type(self, close_type):
        """Check if the user specificed a proper type.

        Type must either be 'discarded' or 'submitted'. If the type
        is wrong, the command will stop and alert the user.
        """
        if close_type not in (SUBMITTED, DISCARDED):
            die("%s is not valid type. Try '%s' or '%s'" %
                (self.options.close_type, SUBMITTED, DISCARDED))

    def main(self, request_id, *args):
        """Run the command."""
        close_type = self.options.close_type
        self.check_valid_type(close_type)

        repository_info, tool = self.initialize_scm_tool()
        server_url = self.get_server_url(repository_info, tool)
        self.root_resource = self.get_root(server_url)

        request = self.get_review_request(request_id)

        if request.status == close_type:
            die("Request request #%s is already %s." % (request_id,
                                                        close_type))

        if self.options.description:
            request.update(data={
                'status': close_type,
                'description': self.options.description,
            })
        else:
            request.update(data={'status': close_type})

        request = self.get_review_request(request_id)

        print "Review request #%s is set to %s." % (request_id, request.status)
