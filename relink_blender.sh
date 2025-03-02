# Remove the existing symlink
unlink ~/Library/Application\ Support/Blender/3.6/scripts/addons/multi_channel_export

# Create a new symlink pointing to your repository's addon folder
ln -s "/Users/lucasertugrul/Documents/Github/RenderRoute/blender-multi-channel-export/addon" ~/Library/Application\ Support/Blender/3.6/scripts/addons/multi_channel_export