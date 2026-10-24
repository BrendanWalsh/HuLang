# Launch Posts

Pre-drafted copy for Show HN, X/Twitter, Bluesky, Reddit, and LinkedIn.
Copy/paste, tweak the URL/screenshot, and fire.

---

## Show HN (Hacker News)

**Title** (max 80 chars, lowercase friendly):

```
Show HN: HuLang -- a natural language compiler that turns .txt into native binaries
```

**URL:** `https://github.com/BrendanWalsh/HuLang`

**Comment** (post immediately after submission):

```
Hi HN -- HuLang is a tongue-in-cheek but functional compiler that takes a natural
language `.txt` file, runs it through an LLM as the parser/codegen, then compiles
the generated C with gcc into a real native binary. No interpreter at runtime.

Pipeline: program.txt -> LLM (frontend) -> gcc (backend) -> ./program

Some details that surprised me building it:
  - Self-repair: if gcc errors, the compiler ships the source + errors back to
    the LLM and asks for a fix (up to 2 retries). Surprisingly resilient.
  - Auto-linker: scans `#include` directives and adds the right `-l` flags.
  - Backends: works with Copilot CLI or Claude Code -- whatever
    you're already authenticated against. No API keys to configure.
  - Examples include a Conway's Game of Life, an in-memory database with a
    SQL-ish REPL, a maze generator, a 600+ line text editor, etc.

It's serious enough to actually build things. It's also clearly the absurd
endpoint of "every generation makes a higher-level language than the last."

The README has the long pitch. Curious what people think.
```

---

## X / Twitter (single post, 280 chars)

```
introducing HuLang: the natural language compiler

write a .txt file in natural language
run `nlc build hello.txt`
get a real ELF binary

LLM is the parser. gcc is the backend. self-repairs if compilation fails.

the obvious endpoint of programming abstraction is here

[github.com/BrendanWalsh/HuLang]
```

(Attach `.github/demo.mp4` (H.264, autoplays inline on X) or the GIF as fallback.)

---

## X / Twitter (thread)

**Tweet 1:**
```
i built a compiler that compiles natural language .txt files into native binaries.

it's called HuLang. the LLM is the parser. gcc is the backend.

write natural language -> get an ELF.

(thread)
```

**Tweet 2:** (attach `.github/demo.mp4` -- autoplays inline on X, or fall back to the GIF)
```
this is the demo. it's compiling a raw-termios terminal text editor written
in natural language. the binary at the end is real. it segfaults if you ask it to.

every generation invents a higher-level language than the last.
this is just the obvious endpoint.
```

**Tweet 3:**
```
it has all the things real compilers have:

  - frontend: parses your source (well, an LLM does)
  - backend: emits optimized native code (gcc -O2)
  - linker: auto-detects which libs to link based on #include
  - error recovery: if gcc fails, it asks the LLM to fix the C, retries
  - 24 example programs in `examples/`
```

**Tweet 4:**
```
the FAQ entry I'm proudest of:

> What about determinism? Will the same .txt always produce the same binary?
> No. This is a feature, not a bug. Every build is a unique artisanal binary,
> hand-crafted by an AI that may or may not be having a good day.
```

**Tweet 5:**
```
MIT licensed. zero API keys -- it shells out to whichever LLM CLI you already
have authenticated (copilot or claude).

if it makes you laugh, makes you think, or makes you slightly nervous about
the future of programming, star the repo:

github.com/BrendanWalsh/HuLang
```

---

## Bluesky (single post, 300 chars)

```
introducing HuLang: a natural language compiler.

write a .txt file in natural language.
run `nlc build hello.txt`.
get a native ELF binary.

LLM is the parser. gcc is the backend. self-repairs if compilation fails.
the obvious endpoint of programming abstraction.

github.com/BrendanWalsh/HuLang
```

---

## Reddit (r/programming, r/compsci, r/MachineLearning)

**Title:**
```
HuLang: I built a compiler where the frontend is an LLM and the output is a real ELF binary
```

**Body:**
```
HuLang takes a natural language `.txt` file and compiles it to a native executable.
The "compiler" pipeline is:

    program.txt -> LLM (generates C) -> gcc (compiles to native) -> ./program

It has all the boring real-compiler stuff:

  - **Auto-linker** -- scans #include directives and adds the right -l flags
    (OpenSSL, ncurses, SQLite, curl, zlib, readline, etc.)
  - **Self-repair** -- if gcc errors, it sends the source + errors back to the
    LLM and asks for a fix. Up to 2 retries.
  - **Multiple backends** -- works with Copilot CLI or Claude Code.
    No API keys to configure; uses whatever you've already authenticated.
  - **Real examples** -- 24 example programs including a graphical chess engine,
    a 3D physics sandbox, a networked procedural world, an agentic researcher,
    Conway's Game of Life, and a raw-termios terminal text editor.

It's a real working tool that's also a knowing parody of "we'll just abstract
one more level." Code is MIT, repo is here:

https://github.com/BrendanWalsh/HuLang

Curious to hear thoughts on:

  - The self-repair loop -- it works better than I expected
  - Whether "natural language as a programming language" has any future
    beyond demos
  - Better example programs to ship with it
```

---

## LinkedIn

```
A weekend project that turned into something I genuinely enjoy:

HuLang -- a "compiler" where you write your program in natural language, and the
output is a real native binary.

The pipeline: `.txt` -> LLM (generates C) -> gcc (compiles to ELF) -> `./program`.

It's tongue-in-cheek but actually works. The repo includes 24 example programs
that compile and run -- from Hello World to a terminal text editor, graphical
chess engine, 3D physics sandbox, networked world, and agentic researcher.

Some real engineering details that made it more interesting than I expected:

  - A self-repair loop: if gcc errors, the compiler sends the C source and the
    error messages back to the LLM and asks for a fix. Up to 2 automatic retries.
  - An auto-linker: scans `#include` directives and adds the right `-l` flags
    so you never think about linker arguments.
  - Backend agnostic: works with Copilot CLI or Claude Code --
    no API keys to configure, it uses whatever you've already authenticated against.

The README opens with an "Abstraction Timeline" walking through every generation
of programming languages. The premise: every generation makes a higher-level
language than the last, and the obvious endpoint is "just say what you want."

MIT licensed. Code: https://github.com/BrendanWalsh/HuLang

Curious what you think -- especially anyone working on developer tools or LLM
tooling.
```

---

## Mastodon (single toot)

```
i built a compiler that turns natural language .txt files into native binaries.

it's called HuLang. the LLM is the parser. gcc is the backend.
auto-linker, self-repair on failure, multiple LLM backends.

it's tongue-in-cheek but it actually works. 24 example programs ship with it.

github.com/BrendanWalsh/HuLang

#opensource #compilers #ai #programming
```

---

## Pre-Launch Checklist

Before you fire any of the above:

- [ ] Repo is set to **Public** (Settings -> General -> Danger zone)
- [ ] `.github/social-preview.png` uploaded via Settings -> General -> Social preview
- [ ] Latest commit on `main` is green (CI badge in README is green)
- [ ] Demo GIF renders on github.com (the camo proxy needs the repo to be public)
- [ ] v0.1.0 release published (Releases -> Draft a new release -> tag `v0.1.0`)
- [ ] GitHub Discussions enabled (optional, but useful)
- [ ] Topics set on the About panel (already done)
- [ ] You're at a desk and free for ~2h to respond to comments after posting

## Post-Launch Tips

- **HN:** Best windows are 8-10am Pacific weekdays. Post the `Show HN` and the
  initial comment within 1 minute of each other. Reply substantively to every
  thoughtful comment in the first 60 minutes -- HN's ranking weights early
  engagement heavily.
- **Twitter/X:** Pin the launch tweet/thread for at least 48h. Reply to every
  quote-tweet that asks a real question.
- **Reddit:** r/programming is unforgiving but fair. Lead with the engineering,
  not the meme. r/MachineLearning may flag it as low-effort -- post in
  r/MachineLearning's "self-promotion Saturday" thread instead if it exists.
- **Bluesky/Mastodon:** Lower volume but warmer audience for "this is fun and
  also real" projects. Less optimization needed.
