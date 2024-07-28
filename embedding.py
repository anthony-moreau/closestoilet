from sentence_transformers import SentenceTransformer


def write_byte_str(byte_str, output):
    output.write(len(byte_str).to_bytes(8))
    output.write(byte_str)


def write_to_output(output, addresses):
    for i in range(len(addresses["labels"])):
        write_byte_str(addresses["labels"][i].encode(), output)
        write_byte_str(addresses["lat"][i].encode(), output)
        write_byte_str(addresses["lon"][i].encode(), output)
        write_byte_str(addresses["embedding"][i].tobytes(), output)

model = SentenceTransformer('intfloat/e5-large-v2')
model.cuda(0)

addresses = {"labels": [], "lat": [], "lon": [], "embedding": []}

with open("adresses-france.csv", encoding="utf8") as source:
    with open("addresses.csv", "wb") as output:
        source.readline()
        i = 0
        line = source.readline()
        while line:
            if len(addresses["labels"]) == 164:
                addresses["embedding"] = model.encode(addresses["labels"])
                write_to_output(output, addresses)
                addresses = {"labels": [], "lat": [], "lon": [], "embedding": []}
            split = line.split(";")
            label = " ".join((split[2], split[4], split[7], split[5]))
            addresses["labels"].append(label)
            addresses["lat"].append(split[13])
            addresses["lon"].append(split[12])
            i += 1
            line = source.readline()
            if i > 263847:
                break
