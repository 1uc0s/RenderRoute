# 1. Navigate to your project directory
cd /Users/lucasertugrul/Documents/Github/RenderRoute

# 2. Remove the lock file first (in case this is the only issue)
rm -f .git/index.lock

# 3. If you still have issues, remove the entire .git directory to completely start over
rm -rf .git

# 4. Initialize a fresh Git repository
git init

# 5. Add your files
git add .

# 6. Commit the files
git commit -m "Initial commit"

# 7. When you're ready to connect to GitHub, you can add a remote and push
# (Replace with your actual GitHub repository URL)
git remote add origin https://github.com/yourusername/RenderRoute.git

# 8. Push to GitHub
git push -u origin main