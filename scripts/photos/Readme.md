# Google Photos

I tend to take more photos when I'm feeling upbeat than when I'm feeling lethargic.

To illustrate this fact, I used [Google Photos Toolkit](https://github.com/xob0t/Google-Photos-Toolkit/) to generate a frequency distribution of all the photos in my library - going back till 2020.

## Sample code

```js
let nextPageId = null;
do {
  const page = await gptkApi.getItemsByTakenDate(nextPageId);
  for (const item of page.items) {
    console.log(item);
  }
  nextPageId = page.nextPageId;
  break;
} while (nextPageId);
```

This is what an Item looks like:
```
creationTimestamp: 1755681434394
dedupKey: "bGvu9Idf7krB_4JjQke56SaW7nI"
descriptionShort: undefined
duration: undefined
geoLocation: Object { coordinates: undefined, name: undefined }
isArchived: false
isFavorite: false
isLivePhoto: false
isOwned: false
isPartialUpload: false
livePhotoDuration: undefined
mediaKey: "AF1QipPpDIZZOyacALuxn-epbwJS_8dLXaGcR5JZixu7"
resHeight: 3240
resWidth: 2160
thumb: "https://photos.fife.usercontent.google.com/pw/AP1GczMyn6zwyyO8zBX3_jupT-pnp6yh-qQN6oix7EOQnt_GfJblmmk3EQlD4Q"
timestamp: 1741936841000
timezoneOffset: 19800000
```