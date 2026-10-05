---
name: package-audit-paused-until-kaste
description: "2026-10-05 Donald quit the package audit until he gets feedback from kaste (forum topic 79298 reply); do not resume, install, test or file anything for it until he says so"
metadata:
  type: project
---

On 2026-10-05 Donald said: "I am quitting the package audit, until feedback from kaste." This overrides [[feedback_run_unattended_dont_ask_to_continue]] and the unattended continuation in [[project_package_audit_campaign_stopped_2026_10_03]].

**State when he stopped:** the ranked list (scratchpad score_pkgs.tsv, rebuilt from `C:\Users\donal\data\st_packages` per [[reference_st_packages_corpus_and_new_audit_order]]) was at rank ~145; the next package would have been HaoGist. Done in the final stretch (all logged in `.package_skill_test_log.md`): RubyTest, CoffeeCompile, FileZilla SFTP Import, TSQLEasy, AndroidImport, DoxyDoc, DocPHPManualer, Colorcoder, PyYapf, Godef, Worksheet, paredit, SourcePawn Completions, Tensorflow, ImagePaste, Simple Print Function. Issues filed in that stretch: SublimeZilla#27, TSQLEasy#30, docphp#15, PyYapf#59, Godef#29, paredit#32, SourcePawnCompletions#17, Sublime-Tensorflow#5, maltize ruby-tests#272.

**Why:** he is waiting for kaste's answer on the forum (topic https://forum.sublimetext.com/t/79298, post #2 asks which packages to test next or other directions) before spending more effort.

**How to apply:** do not install, test, retest or file for the audit. The half-hour check keeps running but only watches mail, his open PRs and issues, and the forum topic for a kaste reply; surface a kaste reply to him in plain words and wait for his word before resuming. Leftovers kept for retests: `D:\yapf test` (yapf venv), `D:\gopath_test` (godef/guru, ~50 MB), `C:\Users\donal\tools\coffee_npm`.
