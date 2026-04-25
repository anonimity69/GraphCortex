from graph_cortex.config.retrieval import SHARDING_MODE, SHARDING_S3_BUCKET


class PropertySharder:
    """
    Offloads heavy text properties to external storage.
    TODO: actually implement the S3 path — right now it just returns a URI stub.
    """
    def __init__(self, mode=SHARDING_MODE, bucket_prefix=SHARDING_S3_BUCKET):
        self.mode = mode
        self.bucket_prefix = bucket_prefix

    def store(self, node_id: str, payload: str) -> str:
        if self.mode == "local":
            return payload
        return f"{self.bucket_prefix}/{node_id}"

    def retrieve(self, ref_uri: str) -> str:
        if self.mode == "local":
            return ref_uri
        return f"Loaded from {self.mode}: {ref_uri}"  # XXX: stub


sharder = PropertySharder()
