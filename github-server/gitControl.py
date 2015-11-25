from github import Github

def getGithubInstance(userid, passwd):
    try:
        g = Github(userid, passwd)
    except:
        return None
    return g
