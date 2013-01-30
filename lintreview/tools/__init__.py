class Tool(object):
    """
    Base class for tools
    """
    options = []

    def check_dependencies(self):
        """
        Used to check for a tools commandline
        executable or other dependencies.
        """
        return True

    def execute(self, review, files, settings=None):
        """
        Execute the tool against the files in a
        pull request. Files will be filtered by
        match_file()
        """
        self.review = review
        if settings:
            self.options = settings
        for f in files:
            if self.match_file(f):
                self.process(f)
        self.post_process(files)

    def match_file(self, filename):
        """
        Used to check if files can be handled by this
        tool. Often this will just file extension checks.
        """

    def process(self, filename):
        """
        Process a single file, and collect
        tool output for each file
        """

    def post_process(self, files):
        """
        Do any post processing required by
        a tool.
        """
        pass
