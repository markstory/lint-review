class Tool(object):
    """
    Base class for tools
    """
    options = []

    def __init__(self, review, options=None):
        self.review = review
        self.options = options

    def check_dependencies(self):
        """
        Used to check for a tools commandline
        executable or other dependencies.
        """
        return True

    def execute(self, files):
        """
        Execute the tool against the files in a
        pull request. Files will be filtered by
        match_file()
        """
        matching_files = []
        for f in files:
            if self.match_file(f):
                matching_files.append(f)
        self.process_files(matching_files)
        self.post_process(files)

    def match_file(self, filename):
        """
        Used to check if files can be handled by this
        tool. Often this will just file extension checks.
        """
        return True

    def process_files(self, files):
        """
        Used to process all files. Can be overridden by tools
        that support linting more than one file at a time.
        """
        for f in files:
            problems = self.process(f)
            if problems:
                self.review.add_problems(f, problems)

    def process(self, filename):
        """
        Process a single file, and collect
        tool output for each file
        """
        return False

    def post_process(self, files):
        """
        Do any post processing required by
        a tool.
        """
        return False
