Localization

How to create a new language if a .pot file does not exist or needs to be updated:
1. Generate a .pot file from the 1-generate-pot-file.bat

2. In the ../resources folder, create the following directory structure: locale-*/[locale name]/LC_MESSAGES

3. Copy the generated .pot file into the LC_MESSAGES folder and rename the filetype to .po

4. *Important* Edit the .po file and fill in the Content-Type and Content-Transfer-Encoding. Have a human fill in all of the msgstr's according to the desired language.
(example:)
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"

5. Drag the .po file into msgfmt.py. The .po file must be in the same folder as msgfmt.py. This will generate a .mo file in the same folder.

6. In resources.py, add the name of the language into getLanguageOptions():