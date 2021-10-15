
from urllib.parse import quote_plus as quote

# create an async request with requests module
def get_similar_words_requests(query: str) -> list:
    """
    Returns a list of similar words to the given query.
    """

    if (not query) or (len(query) < 3):
        return []
    
    import requests
    the_url = ("https://www.google.com/complete/" +
        "search?q=" + query +
        "&cp=0&client=gws-wiz" +
        "&xssi=t&gs_ri=gws-wiz&hl=en-US&authuser=0&" +
        "pq=" + query +
        "&psi=qUycYJ_XLseNkwXX7oGgBg.1620855979375&nolsbt=1&dpr=1")
    query = quote(query.lower().strip())
    resp = requests.get(the_url)
    return parse_google_data(resp.content.decode("utf-8"))


def get_similar_words(query: str) -> list:
    """
    Returns a list of similar words to the given query.
    """

    
    if (not query) or (len(query) < 3):
        return []
    
    import httpx
    the_url = ("https://www.google.com/complete/" +
        "search?q=" + query +
        "&cp=0&client=gws-wiz" +
        "&xssi=t&gs_ri=gws-wiz&hl=en-US&authuser=0&" +
        "pq=" + query +
        "&psi=qUycYJ_XLseNkwXX7oGgBg.1620855979375&nolsbt=1&dpr=1")
    query = quote(query.lower().strip())
    with httpx.Client() as ses:
        resp = ses.get(the_url)
        return parse_google_data(resp.content.decode("utf-8"))


async def get_similar_words_async(query: str) -> list:
    """
    Returns a list of similar words to the given query.
    """

    
    if (not query) or (len(query) < 3):
        return []
    
    import httpx
    the_url = ("https://www.google.com/complete/" +
        "search?q=" + query +
        "&cp=0&client=gws-wiz" +
        "&xssi=t&gs_ri=gws-wiz&hl=en-US&authuser=0&" +
        "pq=" + query +
        "&psi=qUycYJ_XLseNkwXX7oGgBg.1620855979375&nolsbt=1&dpr=1")
    query = quote(query.lower().strip())
    async with httpx.AsyncClient() as ses:
        resp = await ses.get(the_url)
        return parse_google_data(resp.content.decode("utf-8"))


def parse_google_data(gStr: str) -> list:
    """
    Parses the data returned response from the Google API.
    """

    if (not gStr) or (len(gStr) < 2):
        return []
    
    final = ""
    allStrs = []
    firstChild = False
    secondChild = False
    thirdChild = False
    insideStr = False
    childDone = False
    additionalChild = 0
    
    gStr = gStr.replace("\\u003cb\\u003e", "").replace("\\u003c\\/b\\u003e", "")
    for current in gStr:
        if current != '[':
            if current == '"':
                # ensure that we are in correct time line, Steins;Gate.
                if not thirdChild:
                    #Forbidden!
                    # we are only allowed to do operations in
                    # third child, not in any other childs!
                    continue
                
                if not childDone:
                    if insideStr:
                        insideStr = False
                        childDone = True
                    else:
                        insideStr = True
                    continue
                else:
                    continue
            
            # CHAR_S8  = ']'
            if current == ']':
                # ensure that we have already passed the first child.
                # actually I don't know what the hell are these characters
                # at the first of recieved data from google: )]}'.
                # really, what's wrong with them? maybe it's only me
                # whose response is like this.
                # anyway, it won't hurt if I write a checker here.
                if not firstChild:
                    continue
                    
                # we should check if this ended child was
                # an official child or not.
                if additionalChild == 0:
                    # it means this is an official child.

                    # we should check if this ended child
                    # is the third child or not.
                    if thirdChild:
                        # it means third child has been ended.
                        # now our duty is to append it to the
                        # allStrs array.
                        allStrs.append(final)
                        final = ""
                        childDone = False
                        thirdChild = False
                        continue

                    if secondChild:
                        # if the result is not found in google's server,
                        # we will get a response like this:
                        # [[],{"i":"rellowrellow","q":"kikrhTfn3q01Ssg4sD_3SYeA8B4"}]
                        if len(allStrs) == 0:
                            return None

                        # we are done! return all of the slices.
                        return allStrs
                    
                    # no need for check for first child,
                    # since we don't know if its contents is
                    # bullshit or not.
                    # for more information, compare
                    # example09.json and example08.json with each other.
                    # if firstChild {
                    #
                    #}
                    continue
                else:
                    additionalChild -= 1

            if insideStr:
                final += current
            
            continue
        else:
            # check if it's our first child or not.
            if not firstChild:
                firstChild = True
                continue

            # check if it's our second child or not.
            if not secondChild:
                secondChild = True
                continue

            # check if it's our third child or not.
            if not thirdChild:
                thirdChild = True
                continue
            
            # we have at most 3 official children.
            # we need only these children.
            # but in the data, we will have more than these.
            # we don't know how many, maybe 4, maybe 5 or even 6.
            # which is why we have to use counter for them.
            additionalChild += 1
    
    return allStrs

