import hashlib

# used to generate a hash from the strings for the repo config
def generate_unique_hash(
    cache_path:str = '',
    remote_url:str= '',
    branch:str = ''
):
    if not cache_path or not remote_url or not branch:
        return None
    # passed strings will be combined, encoded, and hashed
    combined_string = "".join(cache_path + remote_url + branch)
    encoded_string = combined_string.encode('utf-8')
    hash_object = hashlib.sha256(encoded_string)
    hex_digest = hash_object.hexdigest()
    return hex_digest