#!/usr/bin/env python3
"""A harmless live terminal specimen; exits on Enter."""
print('\033[2J\033[H\n  Basedcode / Terminal colour review\n')
print('  JetBrains Mono • purple working surface • functional colour\n')
for bright in (False, True):
    print('  '+('Bright  ' if bright else 'Regular ')+'  '.join(f'\033[{(90 if bright else 30)+i}m{(90 if bright else 30)+i:2d} Aa\033[0m' for i in range(1,8)))
print('\n  \033[90m// Comments should remain comfortably readable.\033[0m')
print('  \033[34mfunction\033[0m buildTheme(palette) {')
print('    \033[35mconst\033[0m name = \033[32m"Basedcode"\033[0m;')
print('    \033[35mreturn\033[0m { name, version: \033[33m1\033[0m };\n  }\n')
print('  \033[32m+ Added: legible selections\033[0m')
print('  \033[31m- Removed: faint keyboard focus\033[0m')
print('  \033[33m! Warning: review before release\033[0m\n')
print('  \033[48;2;102;54;116m\033[97m Selection: light text on purple \033[0m\n')
input('  Press Enter to close this review. ')
