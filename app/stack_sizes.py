from __future__ import annotations

STACK_SIZE_1 = {
    "wooden axe", "wooden pickaxe", "wooden shovel", "wooden hoe", "wooden sword",
    "stone axe", "stone pickaxe", "stone shovel", "stone hoe", "stone sword",
    "iron axe", "iron pickaxe", "iron shovel", "iron hoe", "iron sword",
    "golden axe", "golden pickaxe", "golden shovel", "golden hoe", "golden sword",
    "diamond axe", "diamond pickaxe", "diamond shovel", "diamond hoe", "diamond sword",
    "netherite axe", "netherite pickaxe", "netherite shovel", "netherite hoe", "netherite sword",
    "leather cap", "leather tunic", "leather pants", "leather boots",
    "leather helmet", "leather chestplate", "leather leggings",
    "chainmail helmet", "chainmail chestplate", "chainmail leggings", "chainmail boots",
    "iron helmet", "iron chestplate", "iron leggings", "iron boots",
    "golden helmet", "golden chestplate", "golden leggings", "golden boots",
    "diamond helmet", "diamond chestplate", "diamond leggings", "diamond boots",
    "netherite helmet", "netherite chestplate", "netherite leggings", "netherite boots",
    "turtle shell", "turtle helmet",
    "shield", "elytra", "trident", "bow", "crossbow", "fishing rod",
    "carrot on a stick", "warped fungus on a stick", "totem of undying",
    "saddle",
    "leather horse armor", "iron horse armor", "golden horse armor", "diamond horse armor",
    "oak boat", "spruce boat", "birch boat", "jungle boat", "acacia boat",
    "dark oak boat", "mangrove boat", "cherry boat", "bamboo raft", "pale oak boat",
    "oak chest boat", "spruce chest boat", "birch chest boat", "jungle chest boat",
    "acacia chest boat", "dark oak chest boat", "mangrove chest boat", "cherry chest boat",
    "bamboo chest raft", "pale oak chest boat",
    "minecart", "chest minecart", "furnace minecart", "hopper minecart",
    "tnt minecart", "command block minecart",
    "written book", "writable book", "book and quill", "enchanted book",
    "potion", "splash potion", "lingering potion",
    "cake", "bed", "white bed", "orange bed", "magenta bed", "light blue bed",
    "yellow bed", "lime bed", "pink bed", "gray bed", "light gray bed", "cyan bed",
    "purple bed", "blue bed", "brown bed", "green bed", "red bed", "black bed",
    "shulker box", "white shulker box", "orange shulker box", "magenta shulker box",
    "light blue shulker box", "yellow shulker box", "lime shulker box", "pink shulker box",
    "gray shulker box", "light gray shulker box", "cyan shulker box", "purple shulker box",
    "blue shulker box", "brown shulker box", "green shulker box", "red shulker box",
    "black shulker box",
    "bundle", "white bundle", "orange bundle", "magenta bundle", "light blue bundle",
    "yellow bundle", "lime bundle", "pink bundle", "gray bundle", "light gray bundle",
    "cyan bundle", "purple bundle", "blue bundle", "brown bundle", "green bundle",
    "red bundle", "black bundle",
}

STACK_SIZE_16 = {
    "ender pearl", "snowball", "egg", "honey bottle", "armor stand",
    "bucket", "water bucket", "lava bucket", "milk bucket", "powder snow bucket",
    "axolotl bucket", "cod bucket", "salmon bucket", "pufferfish bucket",
    "tropical fish bucket", "tadpole bucket",
    "sign", "oak sign", "spruce sign", "birch sign", "jungle sign", "acacia sign",
    "dark oak sign", "mangrove sign", "cherry sign", "bamboo sign", "crimson sign",
    "warped sign", "pale oak sign",
    "oyster",
}


def _normalize(name: str) -> str:
    return " ".join(name.strip().lower().split())


def get_stack_size(item_name: str) -> int:
    key = _normalize(item_name)
    if key in STACK_SIZE_1:
        return 1
    if key in STACK_SIZE_16:
        return 16
    return 64
