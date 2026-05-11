# Fix ReferenceError for lastStageKey

## 1. File
`D:\files\Gproject\src-frontend\src\views\data-management\data-processing\index.vue`

## 2. Issue
A `ReferenceError` occurs because `lastStageKey` is assigned an empty string (`lastStageKey = ''`) on line 408, but the variable is never declared within the scope.

## 3. Fix
Remove the assignment `lastStageKey = ''` from the `resetForNewTask` function.