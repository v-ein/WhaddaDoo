# About

WhaddaDoo is a personal to-do list tool.

- It is freeware.
- It is entirely local and works offline.
- Inspired by Agile practices, it aims to help with prioritization in the first place. Its main purpose is to answer the question, "What should I do now?"

# Development

## DISCLAIMER

When I was starting this project, I had very little Python experience and absolutely no wxPython/wxWidgets knowledge. Even though I try to do my best and improve the code as I learn, it might still look weird here and there.

## Naming conventions

You might have noticed that wxPython does not adhere to PEP 8 naming conventions, at least for method names. This is because it's a wrapper around wxWidgets, which is a C++ library.

Within my subclasses of wxPython classes, I use the same naming convention as in wxPython/wxWidgets - CamelCase method names and all. Otherwise such classes would quickly become a horrible mess of different styles.

For 'pure' Python classes, however, I prefer to use the naming recommended in PEP 8. This might look like an unwise mix of rules in a single project; however, I do have my reasons: you can't avoid PEP 8 names because **all other** libraries, including Python itself, use them. Therefore I try to minimize the area where non-PEP 8 names live.

# License

This project is licensed under the terms of the MIT license. For full license terms, please refer to the file [LICENSE](LICENSE).