# Contribution

## File formatting
File type unix
encoding utf-8
tab should be "4 spaces"


<span style="color:red"> **This is important since python otherwise can show errors when swiching from
linux/windows**  </span>

## Commiting
Before commiting check what is added (just to see if something is unintionally
added)
```
git diff 
```
or if has been staged for the commit
```
git diff --cached 
```

### Tests
Check that the tests run "as expected" before commiting.
```
python setup.py test
```
Don't commit outcommentented test for improved speed (we loose track of what
we can do)
In order to run a single test 
```bash
python setup.py -s test/conflictmanagertest.py
```

## Issues
<span style="color:red"> **When your are working on something add an issue for 
it an assign yourself to it. This means that we can all follow the progress
that is done, and make sure that 2 people don't do same work twice!**
</span>

## Merging
We should merge to the master ONLY when the tests show the expected behavior.
It is in general better to a [git rebase](https://git-scm.com/docs/git-rebase)
since it leaves a cleaner (more logical master), however the simple merge is
also fine.
