with open('requirements.txt', 'rb') as f:
    content = f.read()

# Decode from utf-16-le and remove the BOM
try:
    decoded_content = content.decode('utf-16-le').lstrip('\ufeff')
except UnicodeDecodeError as e:
    # It might be partially decoded, let's try to recover
    # This is a bit of a hack, but might work if the error is at the very end
    decoded_content = content[:e.start].decode('utf-16-le', 'ignore').lstrip('\ufeff')


# Clean up the content
lines = decoded_content.splitlines()
cleaned_lines = []
for line in lines:
    # Remove null bytes and trailing whitespace
    cleaned_line = line.replace('\x00', '').strip()
    if cleaned_line and '"' not in cleaned_line: # Also remove the weird "WeasyPrint" line
        cleaned_lines.append(cleaned_line)

with open('requirements.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(cleaned_lines))

print("requirements.txt has been cleaned and re-encoded to UTF-8.")
