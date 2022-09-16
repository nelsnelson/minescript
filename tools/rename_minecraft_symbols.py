#!/usr/bin/python3

# SPDX-FileCopyrightText: © 2022 Greg Christiana <maxuser@minescript.net>
# SPDX-License-Identifier: MIT

"""Tool for renaming Java symbols between Forge and Fabric mappings.

Usage:
# Translate source with Fabric mappings to Forge mappings:
$ ./rename_minecraft_symbols.py --to_forge <$fabric_src |java-format - > $forge_src

# Translate source with Forge mappings to Fabric mappings:
$ ./rename_minecraft_symbols.py --to_fabric <$forge_src |java-format - > $fabric_src

For an implementation of java-format, see: https://github.com/google/google-java-format
"""

import re
import sys

forge_to_fabric_class_names = (
  ('net.minecraft.client.Minecraft', 'net.minecraft.client.MinecraftClient'),
  ('net.minecraft.client.Screenshot', 'net.minecraft.client.util.ScreenshotRecorder'),
  ('net.minecraft.client.gui.components.EditBox', 'net.minecraft.client.gui.widget.TextFieldWidget'),
  ('net.minecraft.client.gui.screens.ChatScreen', 'net.minecraft.client.gui.screen.ChatScreen'),
  ('net.minecraft.client.gui.screens.Screen', 'net.minecraft.client.gui.screen.Screen'),
  ('net.minecraft.client.player.LocalPlayer', 'net.minecraft.client.network.ClientPlayerEntity'),
  ('net.minecraft.network.chat.Component', 'net.minecraft.text.Text'),
  ('net.minecraft.world.item.ItemStack', 'net.minecraft.item.ItemStack'),
  ('net.minecraft.world.level.Level', 'net.minecraft.world.World'),
  ('net.minecraft.world.level.LevelAccessor', 'net.minecraft.world.WorldAccess'),
  ('net.minecraft.world.level.block.state.BlockState', 'net.minecraft.block.BlockState'),
  ('net.minecraft.world.level.chunk.ChunkAccess', 'net.minecraft.world.chunk.Chunk'),
  ('net.minecraft.world.level.chunk.ChunkSource', 'net.minecraft.world.chunk.ChunkManager'),
)

forge_to_fabric_member_names = (
  ('"f_95573_"', '"field_2382"'),
  ('"input"', '"chatField"'),
  ('Component.nullToEmpty', 'Text.of'),
  ('Screenshot.grab', 'ScreenshotRecorder.saveScreenshot'),
  ('chatEditBox.getCursorPosition', 'chatEditBox.getCursor'),
  ('chatEditBox.getValue', 'chatEditBox.getText'),
  ('chatEditBox.insertText', 'chatEditBox.write'),
  ('chatEditBox.setCursorPosition', 'chatEditBox.setCursor'),
  ('chatEditBox.setTextColor', 'chatEditBox.setEditableColor'),
  ('chatEditBox.setValue', 'chatEditBox.setText'),
  ('chatHud.addRecentChat', 'chatHud.addToMessageHistory'),
  ('chunkManager.getChunkNow', 'chunkManager.getWorldChunk'),
  ('chunkPos.getBlockAt', 'chunkPos.getBlockPos'),
  ('inventory.getContainerSize', 'inventory.size'),
  ('inventory.getItem', 'inventory.getStack'),
  ('itemStack.getTag', 'itemStack.getNbt'),
  ('level.getChunkSource', 'level.getChunkManager'),
  ('minecraft.gameDirectory', 'minecraft.runDirectory'),
  ('minecraft.getCurrentServer', 'minecraft.getCurrentServerEntry'),
  ('minecraft.getMainRenderTarget', 'minecraft.getFramebuffer'),
  ('minecraft.gui.getChat', 'minecraft.inGameHud.getChatHud'),
  ('minecraft.level', 'minecraft.world'),
  ('minecraft.screen', 'minecraft.currentScreen'),
  ('options.keyAttack.setDown', 'options.attackKey.setPressed'),
  ('options.keyDown.setDown', 'options.backKey.setPressed'),
  ('options.keyDrop.setDown', 'options.dropKey.setPressed'),
  ('options.keyJump.setDown', 'options.jumpKey.setPressed'),
  ('options.keyLeft.setDown', 'options.leftKey.setPressed'),
  ('options.keyPickItem.setDown', 'options.pickItemKey.setPressed'),
  ('options.keyRight.setDown', 'options.rightKey.setPressed'),
  ('options.keyShift.setDown', 'options.sneakKey.setPressed'),
  ('options.keySwapOffhand.setDown', 'options.swapHandsKey.setPressed'),
  ('options.keyUp.setDown', 'options.forwardKey.setPressed'),
  ('options.keyUse.setDown', 'options.useKey.setPressed'),
  ('player.chatSigned', 'player.sendChatMessage'),
  ('player.commandUnsigned', 'player.sendCommand'),
  ('player.getCommandSenderWorld', 'player.getEntityWorld'),
  ('player.getCommandSenderWorld', 'player.getEntityWorld'),
  ('player.getHandSlots', 'player.getHandItems'),
  ('player.getXRot', 'player.getPitch'),
  ('player.getYRot', 'player.getYaw'),
  ('player.setXRot', 'player.setPitch'),
  ('player.setYRot', 'player.setYaw'),
  ('playerWorld.dimension', 'playerWorld.getDimension'),
  ('screen.onClose', 'screen.close'),
  ('serverData.ip', 'serverData.address'),
)

def Usage():
  print(
      "Usage: rename_minecraft_symbols.py --to_fabric|--to_forge",
      file=sys.stderr)

def CreateFullNameRewrite(before, after):
  pattern = re.compile(f"^import {before};")
  return lambda s: pattern.sub(f"import {after};", s)

def CreateSimpleNameRewrite(before, after):
  if before[0] == '"':
    pattern = re.compile(before)
    return lambda s: s if s.startswith("import ") else pattern.sub(after, s)
  else:
    pattern = re.compile(f"\\b{before}\\b")
    return lambda s: s if s.startswith("import ") else pattern.sub(after, s)

def RenameForgeToFabric():
  rewrites = []  # List of rewrite functions that take a string to rewrite.

  for forge_name, fabric_name in forge_to_fabric_member_names:
    rewrites.append(CreateSimpleNameRewrite(forge_name, fabric_name))

  for forge_name, fabric_name in forge_to_fabric_class_names:
    rewrites.append(CreateFullNameRewrite(forge_name, fabric_name))

    forge_simple_name = forge_name.split('.')[-1]
    fabric_simple_name = fabric_name.split('.')[-1]
    if forge_simple_name != fabric_simple_name:
      rewrites.append(CreateSimpleNameRewrite(forge_simple_name, fabric_simple_name))

  rewrites.append(lambda s: s.replace('/* Begin Forge only */', '/* Begin Forge only'))
  rewrites.append(lambda s: s.replace('/* End Forge only */', 'End Forge only */'))

  forge_only_pattern = re.compile(f"^( *)(.*) // Forge only$")
  rewrites.append(lambda s: forge_only_pattern.sub(r"\1// Forge only: \2", s))

  ApplyRewritesToStdin(rewrites)

def RenameFabricToForge():
  rewrites = []  # List of rewrite functions that take a string to rewrite.

  for forge_name, fabric_name in forge_to_fabric_member_names:
    rewrites.append(CreateSimpleNameRewrite(fabric_name, forge_name))

  for forge_name, fabric_name in forge_to_fabric_class_names:
    rewrites.append(CreateFullNameRewrite(fabric_name, forge_name))

    forge_simple_name = forge_name.split('.')[-1]
    fabric_simple_name = fabric_name.split('.')[-1]
    if forge_simple_name != fabric_simple_name:
      rewrites.append(CreateSimpleNameRewrite(fabric_simple_name, forge_simple_name))

  rewrites.append(lambda s: s.replace('/* Begin Forge only', '/* Begin Forge only */'))
  rewrites.append(lambda s: s.replace('End Forge only */', '/* End Forge only */'))

  forge_only_pattern = re.compile(f"^ *// Forge only: (.*)")
  rewrites.append(lambda s: forge_only_pattern.sub(r"\1 // Forge only", s))

  ApplyRewritesToStdin(rewrites)

def ApplyRewritesToStdin(rewrites):
  reading_imports = False
  commented_imports = set()
  for line in sys.stdin.readlines():
    if line.startswith('import '):
      reading_imports = True
    if not line.strip().endswith('[norewrite]'):
      for rewrite in rewrites:
        line = rewrite(line)

    if reading_imports and not re.match('(import |// (Fabric|Forge) only: import )', line):
      reading_imports = False
      for commented_import in sorted(commented_imports):
        print(commented_import, end="")

    if re.match('// (Fabric|Forge) only:', line):
      commented_imports.add(line)
    else:
      print(line, end="")


def main(argv):
  if len(argv) != 1:
    Usage()
  elif argv[0] == "--to_fabric":
    RenameForgeToFabric()
  elif argv[0] == "--to_forge":
    RenameFabricToForge()
  else:
    Usage()

if __name__ == "__main__":
  main(sys.argv[1:])
