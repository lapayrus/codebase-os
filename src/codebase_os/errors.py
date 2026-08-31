class CodebaseOSError(Exception):
    """Base class for errors safe to map at the API boundary."""


class RepositoryNotFound(CodebaseOSError):
    pass


class IndexNotReady(CodebaseOSError):
    pass


class PermissionDenied(CodebaseOSError):
    pass


class EvidenceUnavailable(CodebaseOSError):
    pass


class ProviderError(CodebaseOSError):
    pass

