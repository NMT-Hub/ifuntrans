# Place this in your Fish functions folder to make it available immediately
# e.g. ~/.config/fish/functions/envsource.fish
#
# Usage: envsource <path/to/env>

function envsource
  for line in (cat $argv | grep -v '^#')
    # skip empty lines
    if test -z $line
      continue
    end
    set item (string split -m 1 '=' $line)
    # skip line if item[2] is empty
    if test -z $item[2]
      continue
    end
    set -gx $item[1] $item[2]
    echo "Exported key $item[1]"
  end
end

envsource .env_formal
