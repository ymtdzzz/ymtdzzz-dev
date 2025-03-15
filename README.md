# ymtdzzz-dev

My blog

## getting started

```sh
ln -s $(pwd)/images ./gridsome-theme/src/assets/images
cd gridsome-theme
yarn
gridsome develop
```

### On obsidian

```sh
# create a new empty vault
ln -s /path/to/github.com/ymtdzzz/ymtdzzz-dev/content content
mkdir -p gridsome-theme/src/assets
ln -s /path/to/github.com/ymtdzzz/ymtdzzz-dev/gridsome-theme/src/assets/images ./gridsome-theme/src/assets/images
```

In settings

- `New link format`: `Relative path to file`
- `Use [[Wikilinks]]`: `false`
- `Default location for new attachments`: `gridsome-theme/src/assets/images/obsidian`

And install `Attachment Management` plugin by `trganda`

- `Root path to save attachment`: `Copy Obsidian settings`
- `Attachment path`: `${notename}`
- `Attachment format`: `attachment-${date}`

## build

```sh
cd gridsome-theme
gridsome build
```
