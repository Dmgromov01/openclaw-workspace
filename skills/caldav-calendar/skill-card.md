## Description: <br>
Sync and query CalDAV calendars such as iCloud, Google, Fastmail, and Nextcloud using vdirsyncer and khal on Linux. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[asleep123](https://clawhub.ai/user/asleep123) <br>

### License/Terms of Use: <br>


## Use Case: <br>
Developers and agent users use this skill to configure, sync, list, search, create, edit, and delete events in CalDAV-compatible calendars from a Linux command-line environment. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Calendar account credentials and event data may be exposed to the tools the agent operates. <br>
Mitigation: Use app-specific or limited-scope credentials where available, and restrict permissions on credential and calendar cache files. <br>
Risk: Create, edit, delete, or sync commands can change remote calendars. <br>
Mitigation: Review calendar mutation and sync commands before applying them to remote calendars. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/asleep123/skills/caldav-calendar) <br>
- [iCloud CalDAV endpoint](https://caldav.icloud.com/) <br>
- [Fastmail CalDAV endpoint](https://caldav.fastmail.com/dav/calendars/user/EMAIL/) <br>
- [Nextcloud CalDAV path pattern](https://YOUR.CLOUD/remote.php/dav/calendars/USERNAME/) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown with shell command and INI configuration examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires Linux with vdirsyncer and khal available.] <br>

## Skill Version(s): <br>
1.0.1 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
