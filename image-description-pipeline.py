import json
from collections import defaultdict
import os


def parse_image_annotations(categories_file_path: str, output_json: str, coco_file_path: str):
    with open(coco_file_path, 'r') as f:
        coco = json.load(f)

    with open(categories_file_path, 'r') as f:
        categories = json.load(f)

    categories = {category['id']: category for category in categories["categories"]}

    # Build lookup: image_id → file_name
    image_map = {img['id']: img['file_name'] for img in coco['images']}

    # Group annotations by image_id
    image_annotations = defaultdict(set)
    for ann in coco['annotations']:
        image_id = ann['image_id']
        category_id = ann['category_id']
        # category_name = categories[category_id]['name']
        image_annotations[image_id].add(category_id)

    # Build final output — only include images that have at least one annotation
    result = {
        image_map[image_id]: {
            "annotations": [categories[category_id]['description'] for category_id in annotations if
                            not categories[category_id].get('isFreeFluid', False)],
            "window": categories[list(annotations)[0]]['window'] if annotations else "",
            "quadrant": categories[list(annotations)[0]]['quadrant'] if annotations else "",
            "freeFluidSpaceSpace": categories[list(annotations)[0]]['freeFluidSpace'] if annotations else "",
            "hasFreeFluid": categories[list(annotations)[0]]['isFreeFluid'] if annotations else 'false',
        }
        for image_id, annotations in image_annotations.items()
    }

    # Save to file
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def generate_description(image_annotations_path: str, language: str):
    with open(image_annotations_path, 'r') as f:
        image_annotations = json.load(f)

    descriptions = {}
    for image_name, data in image_annotations.items():
        annotations = data["annotations"]
        window = data["window"]
        quadrant = data["quadrant"]
        free_fluid_space = data["freeFluidSpaceSpace"]
        has_free_fluid = data["hasFreeFluid"]

        description_parts = []
        if window:
            description_parts.append(f"Window: {window}")
        if quadrant:
            description_parts.append(f"Quadrant: {quadrant}")
        if free_fluid_space:
            description_parts.append(f"Free Fluid Space: {free_fluid_space}")
        if has_free_fluid:
            description_parts.append("Contains Free Fluid")

        # pt-BR description
        if language == "pt":
            descriptions[
                image_name] = f"{quadrant} imagem eFAST da janela {window}. Os órgãos visíveis são: {", ".join(annotations)}. Líquido livre {"presente" if has_free_fluid else "ausente"} no {free_fluid_space}"
        else:
            descriptions[
                image_name] = f" eFAST image from quadrant {quadrant} and {window} window. Visible organs: {", ".join(annotations)}. Free fluid {"positive" if has_free_fluid else "negative"} in the {free_fluid_space}"

    return descriptions


def generate(coco_file, output, language="en"):
    categories_file = "categories-en.json" if language == "en" else "categories.json"
    parse_image_annotations(categories_file, output, coco_file)
    return generate_description(output, language)


if __name__ == "__main__":
    #test_descriptions = generate(coco_file="./dataset/test/_annotations.coco.json",
    #                             output="image-test-annotations.json")
    valid_descriptions = generate(coco_file="./dataset/valid/_annotations.coco.json",
                                  output="image-valid-annotations.json")
    train_descriptions = generate(coco_file="./dataset/train/_annotations.coco.json",
                                  output="image-train-annotations.json")

    #merged_descriptions = {**test_descriptions, **valid_descriptions, **train_descriptions}
    merged_descriptions = {**valid_descriptions, **train_descriptions}

    print(f"Total descriptions: {len(merged_descriptions)}")

    with open("image-descriptions.json", 'w', encoding='utf-8') as file:
        json.dump(merged_descriptions, file, indent=2, ensure_ascii=False)
