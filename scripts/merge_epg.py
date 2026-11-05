import gzip
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


SOURCES = [
    ("Croatia", "https://www.open-epg.com/files/croatia.xml.gz"),
    ("Bosnia", "https://www.open-epg.com/files/bosnia.xml.gz"),
    ("Serbia", "https://www.open-epg.com/files/serbia1.xml.gz"),
    ("Argentina", "https://www.open-epg.com/files/argentina.xml.gz"),
    ("Brazil 1", "https://www.open-epg.com/files/brazil1.xml.gz"),
    ("Brazil 2", "https://www.open-epg.com/files/brazil2.xml.gz"),
    ("Brazil 3", "https://www.open-epg.com/files/brazil3.xml.gz"),
    ("Brazil 4", "https://www.open-epg.com/files/brazil4.xml.gz"),
    ("Brazil 5", "https://www.open-epg.com/files/brazil5.xml.gz"),
    ("Germany", "https://www.open-epg.com/files/germany.xml.gz"),
    ("Spain", "https://www.open-epg.com/files/spain.xml.gz"),
    ("beIN Sports MENA", "https://al7omed.github.io/bein-epg/guide.xml"),
]


OUTPUT_DIR = Path("docs")
OUTPUT_FILE = OUTPUT_DIR / "international-master.xml.gz"

OUTPUT_DIR.mkdir(exist_ok=True)


def download(url):
    print(f"Downloading: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 EPG-Merger/1.0"
        },
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()

    if url.endswith(".gz"):
        data = gzip.decompress(data)

    return data


master = ET.Element(
    "tv",
    {
        "generator-info-name": "International Master EPG"
    }
)

channel_ids = set()
programme_keys = set()

channel_count = 0
duplicate_channels = 0

programme_count = 0
duplicate_programmes = 0


for source_name, url in SOURCES:

    print("")
    print("=" * 60)
    print(f"Processing: {source_name}")
    print("=" * 60)

    try:
        xml_data = download(url)
        root = ET.fromstring(xml_data)

    except Exception as exc:
        print(f"ERROR processing {source_name}: {exc}")
        raise

    if root.tag != "tv":
        raise ValueError(
            f"{source_name} is not a valid XMLTV document "
            f"(root element is '{root.tag}', expected 'tv')."
        )

    source_channels = root.findall("channel")
    source_programmes = root.findall("programme")

    added_channels = 0
    skipped_channels = 0

    added_programmes = 0
    skipped_programmes = 0


    # ------------------------------------
    # CHANNELS
    # ------------------------------------

    for channel in source_channels:

        channel_id = channel.get("id")

        if not channel_id:
            continue

        if channel_id in channel_ids:

            duplicate_channels += 1
            skipped_channels += 1
            continue

        channel_ids.add(channel_id)
        master.append(channel)

        channel_count += 1
        added_channels += 1


    # ------------------------------------
    # PROGRAMMES
    # ------------------------------------

    for programme in source_programmes:

        channel_id = programme.get("channel")
        start = programme.get("start", "")
        stop = programme.get("stop", "")

        title_node = programme.find("title")

        title = ""

        if title_node is not None and title_node.text:
            title = title_node.text.strip()

        programme_key = (
            channel_id,
            start,
            stop,
            title
        )

        if programme_key in programme_keys:

            duplicate_programmes += 1
            skipped_programmes += 1
            continue

        programme_keys.add(programme_key)

        master.append(programme)

        programme_count += 1
        added_programmes += 1


    print(f"Channels added:       {added_channels}")
    print(f"Duplicate channels:   {skipped_channels}")
    print(f"Programmes added:     {added_programmes}")
    print(f"Duplicate programmes: {skipped_programmes}")


print("")
print("=" * 60)
print("Creating master XMLTV")
print("=" * 60)


tree = ET.ElementTree(master)

ET.indent(tree, space="  ")


with gzip.open(
    OUTPUT_FILE,
    "wb",
    compresslevel=9
) as gz:

    tree.write(
        gz,
        encoding="utf-8",
        xml_declaration=True
    )


# ----------------------------------------
# Validate final compressed document
# ----------------------------------------

print("")
print("Validating compressed master EPG...")

with gzip.open(OUTPUT_FILE, "rb") as gz:

    validation_tree = ET.parse(gz)
    validation_root = validation_tree.getroot()

    if validation_root.tag != "tv":
        raise ValueError(
            "Final master file is not valid XMLTV."
        )


final_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)


print("")
print("=" * 60)
print("MASTER EPG CREATED SUCCESSFULLY")
print("=" * 60)

print(f"Channels:               {channel_count}")
print(f"Duplicate channels:     {duplicate_channels}")
print(f"Programmes:             {programme_count}")
print(f"Duplicate programmes:   {duplicate_programmes}")
print(f"Compressed size:        {final_size:.2f} MB")
print(f"Output:                  {OUTPUT_FILE}")
