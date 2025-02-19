# gitcache
Save bandwidth on duplicate pull requests with a gitcache

### Purpose
With many local hosts that are frequently grabbing the latest update of a remote git repository, significant bandwith can be saved by having a single, local git repo that is constantly updated with the latest version of the remote repo and the other local hosts usig the local cache for pulls.

Updaes (push) still go to the primary repo, but PR's are performed against the local repo.

### Features
- fully configured via TOML file
- clone non-existant local repo
- verify hash between remote branch and local prior to pull
- option to force new clone on start
- option to share current status page accessible over HTTP

### Requirements
You must already have key based authentication enabled for the user that the script/ service will run under (you dont want your script to be blocked by a login request!)

The installer script will run (tested on Ubuntu) to update your environment as needed, including:
- prompting to open a port in IP Tables for access to the Status Page
- Installing/ updating: Python virtual environment (tested on 3.10+) with installed requirements

git, python3, python3-venv, rsync

### Getting Started
Download the installation script to customize:
```
curl -fsSL https://raw.githubusercontent.com/davewat/gitcache/refs/heads/main/install.sh
```

or run fully automated (tested on Ubuntu):
```
# clone the repo:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/davewat/gitcache/refs/heads/main/install.sh)"
```


#### Current State:
```mermaid
flowchart LR
    subgraph Local_Network
        l1[local host 1]
        l2[local host 2]
        l3[local host 3]
        l4[local host 3]
        l5[local host 3]
    end
    
    subgraph Remote_Network
        rr[(remote git repo)]
    end

    l1 -- bandwidth --> rr
    l2 -- bandwidth --> rr
    l3 -- bandwidth --> rr
    l4 -- bandwidth --> rr
    l5 -- bandwidth --> rr
```

#### Future State:
```mermaid
flowchart LR
    subgraph Local_Network
        l1[local host 1]
        l2[local host 2]
        l3[local host 3]
        l4[local host 3]
        l5[local host 3]
        lc[(local git repo cache)]
    end

    subgraph Remote_Network
        rr[(remote git repo)]
    end

    l1 ----> lc
    l2 ----> lc
    l3 ----> lc
    l4 ----> lc
    l5 ----> lc

    lc -- bandwidth --> rr
```