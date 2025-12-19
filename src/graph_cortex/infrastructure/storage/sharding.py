class PropertySharder:
    """
    Experimental interface for property sharding in Phase 1.
    Offloads heavy properties away from graph topology to maintain performance.
    """
    def __init__(self, mode="local"):
        self.mode = mode

    def store(self, node_id: str, payload: str) -> str:
        """
        Stores heavy payload and returns a lightweight reference (e.g. S3 URI or internal ref).
        """
        if self.mode == "local":
            return payload
        else:
            ref_uri = f"s3://ns-dmg-shard/{node_id}"
            return ref_uri

    def retrieve(self, ref_uri: str) -> str:
        """
        Retrieves the heavy payload from the shard.
        """
        if self.mode == "local":
            return ref_uri
        return f"Loaded external content for {ref_uri}"

sharder = PropertySharder()
