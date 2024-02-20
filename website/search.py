import difflib
def search(keywords, search_keyword):
    '''
    Takes a list of keywords and a search keyword as parameters and returns a list of matching keywords from the keywords list.
    This search function is case-insenstive and allows for partial matches.
    '''
    lower_keywords = [keyword.lower() for keyword in keywords]
    close_matches = difflib.get_close_matches(search_keyword.lower(), lower_keywords, n=len(keywords), cutoff=0.5)
    matching_keywords = [keywords[lower_keywords.index(match)] for match in close_matches]
    return matching_keywords
