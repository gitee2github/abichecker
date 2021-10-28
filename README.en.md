# abichecker

#### Description
abichecker is an ABI compatibility check tool. It calls the [abi-compliance-checker](https://github.com/lvc/abi-dumper) and [abi-dumper](https://github.com/lvc/abi-dumper) APIs to analyze rpm and debuginfo packages, implementing ABI compatibility check.

#### Installation

1. Install the **abi-dumper** and **ompliance-checker** tools.

​       `yum install -y abi-dumper abi-compliance-checker`

2. Download the  **abichecker.py**  script.

#### Instructions

1. Create the working directory **/root/checkdir/**, and the directory for storing rpm packages, that is, **libfoo**.
2. Store the .rpm package ***libfoo*-xxx**.**rpm** of libfoo and the debuginfo package **libfoo-debuginfo-*xxx*.rpm** to the **libfoo** directory.
3. Run **python abichecker.py 'libfoo' '/root/checkdir/'**.
4. Store the ABI check result to the **/root/checkdir/libfoo/compat_reports** directory.

#### Contribution

1. Fork this repository.
2. Create the **Feat_*xxx*** branch.
3. Commit your code.
4. Create a Pull Request (PR).



#### Gitee Features

1.  Use Readme_XXX.md to mark README files with different languages, such as Readme_en.md and Readme_zh.md.
2.  Gitee blog: [blog.gitee.com](https://blog.gitee.com)
3.  You can visit [https://gitee.com/explore](https://gitee.com/explore) to learn about excellent open source projects on Gitee.
4.  [GVP](https://gitee.com/gvp) is short for Gitee Most Valuable Project.
5.  User manual provided by Gitee: [https://gitee.com/help](https://gitee.com/help)
6.  Gitee Cover People is a column to display Gitee members' demeanor. Visit  [https://gitee.com/gitee-stars/](https://gitee.com/gitee-stars/)
