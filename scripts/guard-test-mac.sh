#!/usr/bin/env bash
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec /opt/homebrew/opt/dotnet@8/bin/dotnet exec "$ROOT/src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test.dll" "$@"
