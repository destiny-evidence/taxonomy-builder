import { versions, selectedVersion, currentProjectId, loadVersion } from "../../state/vocabulary";

export function VersionSelector() {
  const versionList = versions.value;
  if (versionList.length <= 1) return null;

  function onChange(e: Event) {
    const version = (e.target as HTMLSelectElement).value;
    const projectId = currentProjectId.value;
    if (projectId) {
      loadVersion(projectId, version);
    }
  }

  return (
    <div class="version-selector">
      <select class="version-selector__select" value={selectedVersion.value ?? ""} onChange={onChange}>
        {versionList.map((v) => (
          <option key={v.version} value={v.version}>
            v{v.version} — {v.title}
            {v.pre_release ? " (pre-release)" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
