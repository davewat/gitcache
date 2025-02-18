import os
import asyncio
from aiohttp import web
import datetime
import time
import toml
from pydantic import TypeAdapter
from git import Repo, InvalidGitRepositoryError
from classes import Config, RepoConfig

class git_cache:
    def __init__(self):
        self.config = None
        
    def load_config(self):
        # load self.config
        self.log("Loading config...")
        config_location = self.get_config_location()
        if not config_location:
            self.log("Config file not found. Exiting.")
            exit()
        try:
            with open(config_location, 'r') as f:
                config_data = toml.load(f)
            self.log(f"Config Data: {config_data}")
            outer_adapter = TypeAdapter(Config)
            self.config = outer_adapter.validate_python(config_data)
        except Exception as e:
            self.log(f"Error loading config: {e}")
            exit()
            
    def start(self):
        self.load_config()
        self.log(self.config.repos[0].cache_path)
        
        # build async loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # server options:
        self.check_server_options()
        
        # startup options for repos:
        self.check_startup_repos()
        
        # start the main loop
        self.loop.create_task(self.process_loop())
        self.loop.run_forever()
    
    def log(self,data):
        print(data)
    
    def check_server_options(self):
        if self.config.enable_status_server:
            if self.config.use_bootstrap:
                template_file = './status_template_bootstrap.html'
            else:
                template_file = './status_template.html'
            with open(template_file, 'r') as file:
                self.html_template = file.read()
            
            self.log(f"Starting status server on port {self.config.status_server_port}...")
            self.loop.create_task(self.start_aiohttp_server(self.config.status_server_port))
        
    def check_startup_repos(self):
        # check any startup items for repos:
        # check oif force_clone is enabled:
        for repo_data in self.config.repos:
            if repo_data.force_clone:
                self.log(f"Force cloning {repo_data.cache_path}...")
                self.loop.create_task(self.reclone_repo(repo_data))
                
    async def process_loop(self):
        self.log("Processing...")
        #### do work
        start_time = time.time()
        task_list = [self.update_branch(repo_data) for repo_data in self.config.repos]  # Create multiple tasks
        # Run all tasks concurrently
        await asyncio.gather(*task_list)
        
        # Ensure at least interval seconds have passed
        elapsed_time = time.time() - start_time
        sleep_time = max(0, self.config.sync_interval - elapsed_time)
        if sleep_time > 0:
            self.log(f"Sleeping for {sleep_time:.2f} seconds before restarting...")
            await asyncio.sleep(sleep_time)
        #
        #await asyncio.sleep(self.config.sync_interval)
        self.loop.create_task(self.process_loop())
    
    def get_config_location(self):
        if os.path.exists('/etc/gitcache/config.toml'):
            return '/etc/gitcache/config.toml'
        elif os.path.exists('./config.toml'):
            # Create the folder
            return './config.toml'
        else:
            return None            
            
    def generate_folder(self,folder_path):
        # Check if the folder exists
        if not os.path.exists(folder_path):
            # Create the folder
            os.makedirs(folder_path)
            self.log(f"Folder '{folder_path}' created.")
        else:
            self.log(f"Folder '{folder_path}' already exists.")
    
    async def get_remote_latest_commit(self,remote_url, branch):
        """Fetch the latest commit hash from the remote repository."""
        try:
            result = await asyncio.create_subprocess_exec(
                "git", "ls-remote", remote_url, f"refs/heads/{branch}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            latest_commit_hash = stdout.decode().split()[0] if stdout else None
            return latest_commit_hash
        except Exception as e:
            self.log(f"Error fetching remote commit for branch {branch}: {e}")
            return None

    async def get_local_latest_commit(self,repo_path, branch):
        """Get the latest commit hash from the local repository."""
        try:
            repo = Repo(repo_path)
            if branch in repo.heads:
                return repo.heads[branch].commit.hexsha
            else:
                self.log(f"Branch {branch} does not exist locally.")
                return None
        except Exception as e:
            self.log(f"Error getting local commit for branch {branch}: {e}")
            return None

    async def reclone_repo(self,repo_config:RepoConfig):
        self.log(f"WARNING: {repo_config.cache_path} exists but is not a valid Git repository.")
        self.log("Re-cloning repository...")
        os.system(f"rm -rf {repo_config.cache_path}")  # Remove invalid repo
        await asyncio.create_subprocess_exec(
            "git", "clone", "--bare", repo_config.remote_url, repo_config.cache_path
        )
    
    async def ensure_repo_exists(self,repo_config:RepoConfig):
        """Check if the CACHE_REPO_PATH exists and is a valid Git repo, else clone it."""
        if not os.path.exists(repo_config.cache_path):
            self.log(f"Cloning repository into {repo_config.cache_path}...")
            await asyncio.create_subprocess_exec(
                "git", "clone", "--bare", repo_config.remote_url, repo_config.cache_path
            )
        else:
            try:
                # Check if it is a valid git repo
                repo = Repo(repo_config.cache_path)
                self.log(f"Repository exists at {repo_config.cache_path}.")
            except InvalidGitRepositoryError:
                self.reclone_repo(repo_config)
            except Exception as e:
                self.log(f"FATAL - Error on verifying git repo: {e}")
                self.log('EXITING')
                exit()
    
    async def update_branch(self,repo_config:RepoConfig):            
        # Check if an update is needed and fetch changes if necessary
        remote_commit = await self.get_remote_latest_commit(repo_config.remote_url, repo_config.branch)
        local_commit = await self.get_local_latest_commit(repo_config.cache_path, repo_config.branch)

        # if they do not match, or if either is None
        if remote_commit != local_commit or not local_commit or not remote_commit:
            self.log(f"[{repo_config.branch}] New changes detected! Fetching updates...")
            await self.ensure_repo_exists(repo_config)
            await asyncio.create_subprocess_exec(
                "git", "-C", repo_config.cache_path, "fetch", "origin", repo_config.branch, "--prune"
            )
        else:
            self.log(f"{repo_config.desc}[{repo_config.branch}] Cache is up to date.")
        repo_config.last_updated = int(time.time())
        repo_config.last_updated = datetime.datetime.fromtimestamp(repo_config.last_updated).isoformat()
        
        repo_config.latest_commit = remote_commit
        self.log(f"{repo_config.desc}[{repo_config.branch}] Updated at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{repo_config.desc}[{repo_config.branch}] Latest commit: {remote_commit}")

    
    ### Serve Status:
    def generate_html(self):
        """Generates the HTML table dynamically from data."""
        rows = "".join(f"<tr><td>{row.cache_path}</td><td>{row.remote_url}</td><td>{row.branch}</td><td>{row.last_updated}</td><td>{row.latest_commit}</td></tr>" for row in self.config.repos)
        return self.html_template.format(rows=rows)

    async def handle_request(self,request):
        """Handles incoming HTTP GET requests and returns the HTML page."""
        return web.Response(text=self.generate_html(), content_type="text/html")

    async def handle_404(self,request):
        """Handles all undefined routes (catch-all)."""
        return web.Response(text="404 - Not Found", status=404)

    async def start_aiohttp_server(self,port):
        """Creates and runs the aiohttp web server with a catch-all route."""
        self.web_app = web.Application()
        self.web_app.router.add_get("/", self.handle_request)  # Main route
        self.web_app.router.add_route("*", "/{tail:.*}", self.handle_404)  # Catch-all route

        runner = web.AppRunner(self.web_app)
        await runner.setup()

        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

        print("Serving HTTP on port 8000")

if __name__ == "__main__":
    app = git_cache()
    app.start()